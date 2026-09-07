"""
Day 1 — Knowledge base ingestion into ChromaDB.

Production note: the locked tech stack (Step 5) uses ChromaDB + sentence-transformers
(all-MiniLM-L6-v2), same as the Gov Assistant project. This script uses
sentence-transformers when available, and falls back to ChromaDB's built-in
default embedding function if sentence-transformers/torch are not installed
in the current environment (used here only to validate the pipeline logic).
"""

import json
import os
import json as _json

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb

try:
    from chromadb.utils import embedding_functions
    EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    print("[info] Using sentence-transformers (all-MiniLM-L6-v2) for embeddings.")
except Exception as e:
    EMBED_FN = None
    print(f"[warn] sentence-transformers unavailable ({e}); using ChromaDB default embedding function.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_store")

def build():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tests = json.load(f)

    client = chromadb.PersistentClient(path=DB_PATH)

    # Reset collection each run so this script is safely re-runnable
    try:
        client.delete_collection("lab_tests")
    except Exception:
        pass

    collection = client.create_collection(
        name="lab_tests",
        embedding_function=EMBED_FN,
    ) if EMBED_FN else client.create_collection(name="lab_tests")

    ids, documents, metadatas = [], [], []
    for t in tests:
        ids.append(t["id"])
        # Document text used for retrieval: name + category + English explanation
        documents.append(f'{t["test_name"]} ({t["category"]}): {t["explanation_en"]}')
        metadatas.append({
            "test_name": t["test_name"],
            "category": t["category"],
            "unit": t["unit"],
            "reference_range": t["reference_range"],
            "explanation_en": t["explanation_en"],
            "explanation_ur": t["explanation_ur"],
            "is_qualitative": t.get("is_qualitative", False),
            "normal_value": t.get("normal_value", ""),
            "abnormal_values": _json.dumps(t.get("abnormal_values", [])),
        })

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[ok] Ingested {len(ids)} lab tests into ChromaDB collection 'lab_tests'.")
    print(f"[ok] Store persisted at: {DB_PATH}")
    return collection

if __name__ == "__main__":
    build()
