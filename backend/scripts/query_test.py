"""
Day 1 — Retrieval + known/unknown validation test (FIXED).

Bug fix: the previous version required an exact match against the full
test_name string (e.g. "Hemoglobin (Hb)"), so shorter inputs like
"Hemoglobin" were incorrectly rejected as unknown. This version builds an
alias index (full name, short name before the parenthesis, and the
abbreviation inside it) so any of those forms correctly match.
"""

import os
import json

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb

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

def build_alias_index():
    """Maps every reasonable variant of a test's name -> its canonical test_name.
    e.g. 'hemoglobin' -> 'Hemoglobin (Hb)', 'hb' -> 'Hemoglobin (Hb)'."""
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
    return index

def lookup(test_name: str, alias_index: dict):
    """Returns the canonical test_name if known, else None. Deliberately
    strict beyond alias matching — no fuzzy/partial guessing."""
    return alias_index.get(test_name.strip().lower())

def retrieve(collection, query: str, n_results: int = 1):
    return collection.query(query_texts=[query], n_results=n_results)

def run():
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(
        name="lab_tests",
        embedding_function=EMBED_FN,
    ) if EMBED_FN else client.get_collection(name="lab_tests")

    alias_index = build_alias_index()

    test_cases = [
        "Hemoglobin",           # short name -> should match "Hemoglobin (Hb)"
        "Hb",                   # abbreviation -> should also match
        "Fasting Blood Sugar",  # short name -> should match "Fasting Blood Sugar (FBS)"
        "Troponin I",           # genuinely not in our ~24-test list -> must be rejected
    ]

    print("=" * 60)
    for case in test_cases:
        print(f"\nInput test name: {case}")
        canonical = lookup(case, alias_index)
        if not canonical:
            print("  -> VALIDATION: unknown test")
            print('  -> OUTPUT: "This test is not yet supported. No guessing — please consult a healthcare professional about this result."')
            continue

        print(f"  -> VALIDATION: known test (matched to '{canonical}'), proceeding to retrieval")
        results = retrieve(collection, canonical, n_results=1)
        meta = results["metadatas"][0][0]
        print(f"  -> Retrieved: {meta['test_name']} | Reference range: {meta['reference_range']} {meta['unit']}")
        print(f"  -> Explanation (EN): {meta['explanation_en'][:100]}...")
        print(f"  -> Explanation (UR): {meta['explanation_ur'][:60]}...")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    run()
