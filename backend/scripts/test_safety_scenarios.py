"""
Day 7 — Automated safety scenario tests.

Covers everything testable WITHOUT a live embedding model or real OCR
(validation logic, abnormal-checking, medicine lookup, parsing). Scenarios
that need the real RAG retrieval or real image OCR are listed separately
in DAY7_TEST_REPORT.md for you to run on your machine.

Run with: python scripts/test_safety_scenarios.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.knowledge import lookup_canonical, _load_alias_index
from app.abnormal_check import check_abnormal
from app.medicine import lookup_medicine
from app.report_parser import parse_report_text

passed = 0
failed = 0


def check(description, condition):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"[{status}] {description}")


print("=" * 70)
print("SCENARIO 1 & 2: Known test, normal/abnormal value classification")
print("=" * 70)
check(
    "Hemoglobin 10.5 (below 12.0-15.5 female range) -> abnormal_low",
    check_abnormal("10.5", "13.5-17.5 (male), 12.0-15.5 (female)") == "abnormal_low",
)
check(
    "Hemoglobin 14.0 (within range) -> normal",
    check_abnormal("14.0", "13.5-17.5 (male), 12.0-15.5 (female)") == "normal",
)
check(
    "Creatinine 1.8 (above 0.6-1.3 range) -> abnormal_high",
    check_abnormal("1.8", "0.7-1.3 (male), 0.6-1.1 (female)") == "abnormal_high",
)

print("\n" + "=" * 70)
print("SCENARIO 3: Unknown test -> not supported, no guessing")
print("=" * 70)
check(
    "'MRI Brain' is not in the known-test alias index",
    lookup_canonical("MRI Brain") is None,
)
check(
    "'Troponin I' is not in the known-test alias index",
    lookup_canonical("Troponin I") is None,
)
check(
    "Known test 'Hemoglobin' IS found (sanity check the index isn't empty)",
    lookup_canonical("Hemoglobin") is not None,
)

print("\n" + "=" * 70)
print("SCENARIO 4: No diagnostic-claim language in explanations")
print("=" * 70)
import json
with open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base.json"),
    encoding="utf-8",
) as f:
    tests = json.load(f)
risky_phrases = ["you have", "this means you have", "diagnosis", "you are diabetic", "you suffer from"]
diagnostic_free = all(
    not any(phrase in t["explanation_en"].lower() for phrase in risky_phrases) for t in tests
)
check(f"All {len(tests)} lab test explanations contain no diagnostic-claim language", diagnostic_free)

with open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "medicine_info.json"),
    encoding="utf-8",
) as f:
    meds = json.load(f)
med_diagnostic_free = all(
    not any(phrase in m["purpose_en"].lower() for phrase in risky_phrases) for m in meds
)
check(f"All {len(meds)} medicine descriptions contain no diagnostic-claim language", med_diagnostic_free)

print("\n" + "=" * 70)
print("SCENARIO 5 & 6: Medicine known/unknown lookup")
print("=" * 70)
check("'Panadol' (brand) resolves to a supported medicine", lookup_medicine("Panadol")["supported"])
check("'paracetamol' (generic, lowercase) resolves", lookup_medicine("paracetamol")["supported"])
check("'Napa' (brand) resolves", lookup_medicine("Napa")["supported"])
check("'RandomUnknownDrugXYZ' is correctly NOT supported", not lookup_medicine("RandomUnknownDrugXYZ")["supported"])

print("\n" + "=" * 70)
print("SCENARIO 7 & 8: Multiple values / mixed known+unknown in one parse")
print("=" * 70)
sample_report = """
Hemoglobin (Hb)      11.2   g/dL   (13.5-17.5)
White Blood Cell Count  9800   cells/mcL  (4500-11000)
Some Unlisted Test XYZ  42   units  (10-50)
Fasting Blood Sugar (FBS)  126   mg/dL  (70-100)
"""
entries = parse_report_text(sample_report)
check(f"Parser extracted {len(entries)} entries from a 4-line mixed report (expected 4)", len(entries) == 4)
known_count = sum(1 for e in entries if lookup_canonical(e["test_name"]) is not None)
unknown_count = len(entries) - known_count
check(
    f"Of those, {known_count} are known and {unknown_count} is/are correctly unknown (expected 3 known, 1 unknown)",
    known_count == 3 and unknown_count == 1,
)

print("\n" + "=" * 70)
print("SCENARIO 10: Blank/garbage OCR text -> no crash, empty result (not a guess)")
print("=" * 70)
try:
    blank_entries = parse_report_text("")
    garbage_entries = parse_report_text("asdkjalksjd ///// 92384 !!! blah blah")
    check("Empty OCR text produces zero entries without crashing", blank_entries == [])
    check("Garbage OCR text produces zero entries without crashing (no false matches)", garbage_entries == [])
except Exception as e:
    check(f"Blank/garbage input did not crash the parser (raised: {e})", False)

print("\n" + "=" * 70)
print(f"RESULT: {passed} passed, {failed} failed")
print("=" * 70)
if failed > 0:
    sys.exit(1)
