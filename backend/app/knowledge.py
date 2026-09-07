"""
Component 3 (Data Validation) + Component 4 (Knowledge Retrieval) as a
reusable module, so both the CLI test scripts and the FastAPI app share
the exact same validation/retrieval logic (no duplicated, drifting copies).
"""

import os

# Bug fix: ChromaDB re-verifies the embedding model against Hugging Face on
# every collection load, even though the model is already cached locally
# after the first download. If the network hiccups at that moment (DNS
# failure, flaky connection), this crashes the whole request. Forcing
# offline mode makes it use the cached model directly — no network needed
# once the model has been downloaded once (which it already has).
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import json
import chromadb
from app.abnormal_check import check_abnormal, check_qualitative
import json as _json

try:
    from chromadb.utils import embedding_functions
    EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
except Exception:
    EMBED_FN = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_store")

from app.abnormal_check import check_abnormal
from app.doctor_questions import get_doctor_questions
from app.llm_generation import enhance_explanation

_alias_index = None
_collection = None

def _load_alias_index():
    global _alias_index
    if _alias_index is not None:
        return _alias_index
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tests = json.load(f)
    index = {}
    for t in tests:
        canonical = t["test_name"]
        index[canonical.strip().lower()] = canonical
        if "(" in canonical and ")" in canonical:
            short_name = canonical.split("(")[0].strip()
            abbreviation = canonical.split("(")[1].replace(")", "").strip()
            index[short_name.lower()] = canonical
            index[abbreviation.lower()] = canonical
        for extra_alias in t.get("aliases", []):
            index[extra_alias.strip().lower()] = canonical
    _alias_index = index
    return _alias_index

def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    client = chromadb.PersistentClient(path=DB_PATH)
    _collection = client.get_collection(
        name="lab_tests", embedding_function=EMBED_FN
    ) if EMBED_FN else client.get_collection(name="lab_tests")
    return _collection

def is_known_test(test_name: str) -> bool:
    return lookup_canonical(test_name) is not None


def _load_category_index():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tests = json.load(f)
    return {t["test_name"]: t["category"] for t in tests}

def lookup_canonical(test_name: str):
    """
    Returns the canonical test_name if known, else None.
    Two-pass matching:
    1. Exact match against the alias index (fast, precise)
    2. Substring fallback: checks BOTH ways —
       a. If a known alias appears in the input (short in long) e.g., "MCH" in "MeanCorpuscularHemoglobin"
       b. If the input appears in a known alias (long in short) e.g., "MeanCorpuscularHemoglobin" in "MCH"
    This handles "HIV" <-> "Human Immunodeficiency Virus" AND vice versa for all tests.
    """
    import re as _re

    def normalize(s: str) -> str:
        return _re.sub(r"[^a-z0-9]", "", s.lower())

    index = _load_alias_index()
    normalized_input = normalize(test_name)
    
    # 1. Exact match
    exact = index.get(test_name.strip().lower())
    if exact:
        return exact

    # 2. Edge case: empty input
    if not normalized_input:
        return None

    # 3. Substring fallback (BOTH directions + short aliases allowed)
    for alias, canonical in index.items():
        normalized_alias = normalize(alias)
        # Allow short aliases like "MCH" while avoiding overly broad matches.
        if len(normalized_alias) >= 3:
            # Check BOTH ways: "mch" in "meancorpuscularhemoglobin"
            # OR "meancorpuscularhemoglobin" in "mch"
            if normalized_alias in normalized_input or normalized_input in normalized_alias:
                return canonical

    return None

def get_test_info(test_name: str, value: str = None, normal_range: str = None, category: str = None):
    """
    Main entry point. Uses report's normal_range FIRST if provided.
    Falls back to database if report range is missing.
    """
    canonical = lookup_canonical(test_name)
    
    # --- CASE 1: KNOWN TEST ---
    if canonical:
        collection = _get_collection()
        results = collection.query(query_texts=[canonical], n_results=1)
        meta = results["metadatas"][0][0]
        
        # PRIORITY: Use report's range if provided, else use database range
        final_range = normal_range if normal_range and normal_range.strip() else meta["reference_range"]
        
        # Check abnormal using the final range
        abnormal_status = check_abnormal(value, final_range) if value is not None else None
        doctor_questions = get_doctor_questions(meta["category"], abnormal_status)

        explanation_en, explanation_ur = enhance_explanation(
            test_name=meta["test_name"],
            value=value,
            abnormal_status=abnormal_status,
            static_explanation_en=meta["explanation_en"],
            static_explanation_ur=meta["explanation_ur"],
            reference_range=final_range,
        )

        return {
            "supported": True,
            "test_name": meta["test_name"],
            "value": value,
            "unit": meta["unit"],
            "normal_range": final_range,  # Show the range used (report priority)
            "category": meta["category"],
            "abnormal_status": abnormal_status,
            "explanation_en": explanation_en,
            "explanation_ur": explanation_ur,
            "doctor_questions": doctor_questions,
        }
    
    # --- CASE 2: UNKNOWN TEST ---
    result = {
        "supported": False,
        "test_name": test_name,
        "value": value,
        "unit": None,
        "normal_range": normal_range,
        "category": category if category else "Other",
        "abnormal_status": None,
        "explanation_en": "This test is not yet supported in our verified database. Please consult a healthcare professional.",
        "explanation_ur": "یہ ٹیسٹ ہمارے تصدیق شدہ ڈیٹا بیس میں شامل نہیں ہے۔ براہ کرم ڈاکٹر سے رجوع کریں۔",
        "doctor_questions": ["Please ask your doctor about this result."],
    }
    
    # If we have BOTH a value AND a normal_range from the image, do a deterministic comparison
    if value is not None and normal_range:
        status = check_abnormal(value, normal_range)
        
        status_text_en = {
            "normal": "within the normal reference range.",
            "abnormal_low": "below the normal reference range (LOW).",
            "abnormal_high": "above the normal reference range (HIGH).",
            "range_unclear": "could not be evaluated clearly against the reference range.",
            "value_unparseable": "could not be parsed as a number.",
        }.get(status, "could not be evaluated.")
        
        status_text_ur = {
            "normal": "عام حوالہ جاتی حد کے اندر ہے۔",
            "abnormal_low": "عام حوالہ جاتی حد سے کم ہے (کم)۔",
            "abnormal_high": "عام حوالہ جاتی حد سے زیادہ ہے (زیادہ)۔",
            "range_unclear": "حوالہ جاتی حد کے خلاف واضح طور پر تشخیص نہیں ہو سکی۔",
            "value_unparseable": "نمبر کے طور پر پارس نہیں ہو سکی۔",
        }.get(status, "تشخیص نہیں ہو سکی۔")

        result["abnormal_status"] = status
        result["explanation_en"] = f"Your {test_name} result is {value}. The reference range printed on the report is {normal_range}. This value is {status_text_en} Please discuss this result with your healthcare provider."
        result["explanation_ur"] = f"آپ کے {test_name} کا نتیجہ {value} ہے۔ رپورٹ پر طباعت شدہ حوالہ جاتی حد {normal_range} ہے۔ یہ قدر {status_text_ur} براہ کرم اس نتیجے کے بارے میں اپنے ڈاکٹر سے مشورہ کریں۔"
        result["doctor_questions"] = get_doctor_questions(category if category else "Other", status)
    
    return result