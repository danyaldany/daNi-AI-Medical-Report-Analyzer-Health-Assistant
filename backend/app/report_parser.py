"""
Parses raw OCR text (Component 2 output) into structured entries:
{test_name, raw_value, unit}. This is intentionally a simple, transparent
regex-based parser rather than an LLM call — parsing structure from text is
a good fit for deterministic rules, and keeping the LLM out of this step
reduces hallucination risk.

Expected line format (matches common lab report layouts):
    Test Name       123.4   unit   (reference range)

This is a best-effort parser. Whatever it extracts is ALWAYS shown to the
user for manual confirmation/edit before analysis (Component 3) — so a
missed or misparsed line is a UX inconvenience, never a silent safety issue.
"""

import re

# Matches: <name>  <number>  <unit>  (anything else, ignored)
# NOTE: uses \s+ (one or more spaces) rather than \s{2,} -- real OCR output
# (verified with Tesseract) often normalizes multi-space table padding down
# to single spaces, so requiring 2+ spaces was silently dropping valid
# lines. This was caught during Day 7 testing.
LINE_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z()\s/]+?)\s+"
    r"(?P<value>-?\d+\.?\d*)\s+"
    r"(?P<unit>[A-Za-z%/]+)"
)


def parse_report_text(raw_text: str):
    """
    Returns a list of dicts: [{"test_name": ..., "value": ..., "unit": ..., "normal_range": ...}]
    """
    entries = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Try the primary pattern: NAME VALUE UNIT
        match = LINE_PATTERN.match(line)
        if match:
            entries.append({
                "test_name": match.group("name").strip(),
                "value": match.group("value").strip(),
                "unit": match.group("unit").strip(),
                "normal_range": "",  # Primary pattern doesn't capture range
            })
            continue
        
        # ---- NEW FALLBACK: Try to extract unit from the normal_range ----
        # Try to find a pattern like: NAME VALUE RANGE UNIT
        # e.g. "S. Creatinine 0.8 M:0.5-1.6 mg/dl"
        # e.g. "Blood Sugar R.F N/A F-60-110 mg/dl"
        
        # Find test name (starts with letters and spaces/slashes/parentheses)
        name_match = re.match(r"^([A-Za-z][A-Za-z()\s/\.]+?)\s+", line)
        if not name_match:
            continue
        test_name = name_match.group(1).strip()
        
        # Remove the name from the line to parse the rest
        rest = line[len(name_match.group(0)):].strip()
        
        # Try to find a value (number or N/A)
        value_match = re.search(r"^([\d\.]+|N/A)\s*", rest)
        if not value_match:
            continue
        value = value_match.group(1)
        rest = rest[len(value_match.group(0)):].strip()
        
        # Now try to find a unit (mg/dl, g/dl, U/L, etc.) at the end of the string
        unit_match = re.search(r"([a-zA-Z]+/[a-zA-Z]+|[a-zA-Z]+%?)\s*$", rest)
        unit = unit_match.group(1) if unit_match else ""
        if unit:
            rest = rest[:len(rest) - len(unit_match.group(0))].strip()
        
        # The remaining rest is the normal_range
        normal_range = rest.strip()
        
        if test_name and value:
            entries.append({
                "test_name": test_name,
                "value": value,
                "unit": unit,
                "normal_range": normal_range,
            })
    
    return entries


def find_known_test_names(raw_text: str, known_aliases: dict):
    """
    Fallback for real-world reports where the strict name+value+unit pattern
    fails (common cause: handwritten values, or multi-column table layouts
    that confuse line-based parsing -- confirmed against a real report photo
    during Day 7 testing). Printed test NAMES are usually still readable
    even when the handwritten result and table layout are not.

    Scans raw_text for any occurrence of a known test name/alias and
    returns pre-filled rows with an EMPTY value -- so the user only needs
    to type the number, not retype the whole test name. This never guesses
    a value; it only recognizes a name that is genuinely, deterministically
    present in the OCR text (a substring match against the verified alias
    list, punctuation-normalized -- e.g. OCR's "S.G.P.T" still matches the
    "SGPT" alias), which is a materially different and safer claim.

    known_aliases: the alias index dict from knowledge._load_alias_index()
    (alias string -> canonical test_name).
    """
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    text_normalized = normalize(raw_text)
    found_canonical = set()
    for alias, canonical in known_aliases.items():
        alias_normalized = normalize(alias)
        if len(alias_normalized) < 3:
            continue  # skip very short aliases (too many false substring hits)
        if alias_normalized in text_normalized:
            found_canonical.add(canonical)

    return [{"test_name": name, "value": "", "unit": ""} for name in sorted(found_canonical)]
