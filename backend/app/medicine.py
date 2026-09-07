"""
Component 6 (Medicine Info Lookup) — deliberately independent from
knowledge.py (lab test retrieval). Same known/unknown safety pattern:
anything outside the verified list returns "not supported", never a guess.

NOTE: medicine_info.json is a starter set of ~14 common medicines for the
MVP demo. It is not a finalized, comprehensively sourced dataset — treat
it as a starting point to expand/verify, not an authoritative reference.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "medicine_info.json")

_alias_index = None
_by_id = None

def _load():
    global _alias_index, _by_id
    if _alias_index is not None:
        return
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        medicines = json.load(f)

    alias_index = {}
    by_id = {}
    for m in medicines:
        by_id[m["id"]] = m
        generic = m["generic_name"]
        alias_index[generic.strip().lower()] = m["id"]
        # Same alias-splitting fix as knowledge.py: "Paracetamol (Acetaminophen)"
        # must also match on "paracetamol" and "acetaminophen" individually.
        if "(" in generic and ")" in generic:
            short_name = generic.split("(")[0].strip()
            alt_name = generic.split("(")[1].replace(")", "").strip()
            alias_index[short_name.lower()] = m["id"]
            alias_index[alt_name.lower()] = m["id"]
        for brand in m.get("common_brands_pk", []):
            alias_index[brand.strip().lower()] = m["id"]
    _alias_index = alias_index
    _by_id = by_id

def lookup_medicine(name: str):
    """
    Main entry point for Component 6.
    Returns medicine info if known (matched by generic name or a common
    Pakistan brand name), or a 'not_supported' response if unknown.
    """
    _load()
    med_id = _alias_index.get(name.strip().lower())
    if not med_id:
        return {
            "supported": False,
            "medicine_name": name,
            "message": "This medicine is not yet in our verified list. No guessing — please consult a doctor or pharmacist about it.",
        }

    m = _by_id[med_id]
    return {
        "supported": True,
        "generic_name": m["generic_name"],
        "common_brands_pk": m["common_brands_pk"],
        "category": m["category"],
        "purpose_en": m["purpose_en"],
        "purpose_ur": m["purpose_ur"],
        "general_notes_en": m["general_notes_en"],
        "general_notes_ur": m["general_notes_ur"],
    }
