"""
Deterministic abnormal-value flagging. Deliberately NOT an LLM call — parsing
a number and comparing it to a range is a good fit for simple rules, and
keeping this deterministic means flagging is 100% reproducible and testable.

Reference ranges in knowledge_base.json are free-text (e.g. "13.5-17.5
(male), 12.0-15.5 (female)", "under 140", "0.4-4.0"). This module parses the
common patterns. When a range can't be confidently parsed (e.g. multi-tier
ranges like HbA1c's), it returns "range_unclear" rather than guessing --
consistent with the project's no-guessing safety principle.
"""

import re

SIMPLE_RANGE = re.compile(r"^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$")
DASH_RANGE = re.compile(r"(\d+\.?\d*)\s*[-–—]\s*(\d+\.?\d*)")
UNDER_PATTERN = re.compile(r"^under\s+(\d+\.?\d*)$", re.IGNORECASE)
OVER_PATTERN = re.compile(r"^over\s+(\d+\.?\d*)$", re.IGNORECASE)
GENDER_SPLIT = re.compile(
    r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\(male\).*?(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\(female\)",
    re.IGNORECASE,
)
GENDER_SPLIT_COLON = re.compile(
    r"M\s*:\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*).*?F\s*:\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)",
    re.IGNORECASE,
)
GENDER_OVER_SPLIT = re.compile(
    r"over\s+(\d+\.?\d*)\s*\(male\).*?over\s+(\d+\.?\d*)\s*\(female\)",
    re.IGNORECASE,
)
# Add this regex near the top with other regexes
SINGLE_GENDER_RANGE = re.compile(r"[MF]\s*:\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)", re.IGNORECASE)
QUALITATIVE_POSITIVE = re.compile(r"(positive|reactive|present|detected|abnormal)", re.IGNORECASE)
QUALITATIVE_NEGATIVE = re.compile(r"(negative|non-reactive|absent|not detected|normal)", re.IGNORECASE)

def _strip_trailing_note(range_text: str) -> str:
    if "male" in range_text.lower() or "female" in range_text.lower():
        return range_text
    return re.sub(r"\s*\([^)]*\)\s*$", "", range_text).strip()

def parse_bounds(reference_range: str):
    text = reference_range.strip()
    
    gender_match = GENDER_SPLIT.search(text)
    if gender_match:
        lows = [float(gender_match.group(1)), float(gender_match.group(3))]
        highs = [float(gender_match.group(2)), float(gender_match.group(4))]
        return (min(lows), max(highs))
        
    gender_colon_match = GENDER_SPLIT_COLON.search(text)
    if gender_colon_match:
        lows = [float(gender_colon_match.group(1)), float(gender_colon_match.group(3))]
        highs = [float(gender_colon_match.group(2)), float(gender_colon_match.group(4))]
        return (min(lows), max(highs))
        
    gender_over_match = GENDER_OVER_SPLIT.search(text)
    if gender_over_match:
        lows = [float(gender_over_match.group(1)), float(gender_over_match.group(2))]
        return (min(lows), None)
    
    # ---- NEW: Single Gender Range (e.g., "M:0.5-1.6") ----
    single_gender_match = SINGLE_GENDER_RANGE.search(text)
    if single_gender_match:
        return (float(single_gender_match.group(1)), float(single_gender_match.group(2)))
    
    clean = _strip_trailing_note(text)
    simple_match = SIMPLE_RANGE.match(clean)
    if simple_match:
        return (float(simple_match.group(1)), float(simple_match.group(2)))

    dash_match = DASH_RANGE.search(text)
    if dash_match:
        return (float(dash_match.group(1)), float(dash_match.group(2)))
        
    under_match = UNDER_PATTERN.match(clean)
    if under_match:
        return (None, float(under_match.group(1)))
        
    over_match = OVER_PATTERN.match(clean)
    if over_match:
        return (float(over_match.group(1)), None)
        
    return None

def check_qualitative(value: str, normal_value: str, abnormal_values: list):
    """
    For Positive/Negative-style results. Case-insensitive, whitespace-tolerant.
    Returns "normal", "abnormal", or "value_unparseable" (never guesses).
    """
    v = str(value).strip().lower()
    if v == str(normal_value).strip().lower():
        return "normal"
    if v in [str(a).strip().lower() for a in (abnormal_values or [])]:
        return "abnormal"
    return "value_unparseable"

def check_abnormal(value: str, reference_range: str):
    """
    Returns one of: "normal", "abnormal_low", "abnormal_high",
    "range_unclear", or "value_unparseable".
    Now supports qualitative (Positive/Negative) values.
    """
    raw_value = str(value).strip()
    
    # --- QUALITATIVE CHECK (Positive/Negative) ---
    # If the reference range is "Negative" (qualitative) or contains "Negative"
    if "negative" in reference_range.lower() or "positive" in reference_range.lower():
        # Check if value is Positive/Reactive/etc.
        if QUALITATIVE_POSITIVE.search(raw_value):
            return "abnormal_high"  # Treat as abnormal
        elif QUALITATIVE_NEGATIVE.search(raw_value):
            return "normal"
        else:
            return "range_unclear"

    # --- QUALITATIVE VALUE IN A NUMERIC TEST ---
    qualitative_keywords = [
        "positive",
        "negative",
        "reactive",
        "non-reactive",
        "nonreactive",
        "detected",
        "present",
    ]
    is_qualitative_value = any(keyword in raw_value.lower() for keyword in qualitative_keywords)
    range_has_qualitative_ref = "negative" in reference_range.lower() or "positive" in reference_range.lower()

    if is_qualitative_value and not range_has_qualitative_ref:
        # Numeric test receiving qualitative input cannot be compared numerically.
        return "range_unclear"
    
    # --- NUMERIC CHECK ---
    try:
        match = re.search(r"[-+]?\d*\.?\d+", raw_value)
        if match:
            cleaned_value = match.group()
        else:
            cleaned_value = raw_value
        numeric_value = float(cleaned_value)
    except (ValueError, TypeError):
        return "value_unparseable"

    bounds = parse_bounds(reference_range)
    if bounds is None:
        return "range_unclear"

    low, high = bounds
    if low is not None and numeric_value < low:
        return "abnormal_low"
    if high is not None and numeric_value > high:
        return "abnormal_high"
    return "normal"