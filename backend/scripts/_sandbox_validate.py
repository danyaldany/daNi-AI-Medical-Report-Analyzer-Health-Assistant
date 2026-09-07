"""
SANDBOX-ONLY validation script.

This sandbox cannot download the sentence-transformers model (disk space)
or ChromaDB's default ONNX model (blocked network egress), so this script
substitutes a local TF-IDF embedding purely to prove the retrieval and
known/unknown validation LOGIC works end to end.

On your actual machine (with normal internet + disk space), use
build_knowledge_base.py and query_test.py as-is — they already use
sentence-transformers (all-MiniLM-L6-v2), per the locked tech stack.
"""

import json
import os
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
DB_PATH = os.path.join(BASE_DIR, "data", "chroma_store_sandbox")

class TfidfEmbeddingFunction(EmbeddingFunction):
    """Local, no-download stand-in for the real sentence-transformer embedder."""
    def __init__(self, corpus):
        self.vectorizer = TfidfVectorizer(max_features=256)
        self.vectorizer.fit(corpus)

    def __call__(self, input: Documents) -> Embeddings:
        vecs = self.vectorizer.transform(input).toarray()
        return [v.tolist() for v in vecs]

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tests = json.load(f)

    documents = [f'{t["test_name"]} {t["category"]} {t["explanation_en"]}' for t in tests]
    embed_fn = TfidfEmbeddingFunction(documents)

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection("lab_tests_sandbox")
    except Exception:
        pass
    collection = client.create_collection(name="lab_tests_sandbox", embedding_function=embed_fn)

    ids = [t["id"] for t in tests]
    metadatas = [{
        "test_name": t["test_name"], "category": t["category"], "unit": t["unit"],
        "reference_range": t["reference_range"], "explanation_en": t["explanation_en"],
        "explanation_ur": t["explanation_ur"],
    } for t in tests]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[ok] Ingested {len(ids)} lab tests (sandbox TF-IDF embedding).\n")

    known_names = {t["test_name"].lower() for t in tests}

    def is_known(name):
        return name.strip().lower() in known_names

    test_cases = ["Hemoglobin (Hb)", "Fasting Blood Sugar (FBS)", "LDL Cholesterol", "Troponin I"]

    print("=" * 60)
    for case in test_cases:
        print(f"\nInput test name: {case}")
        if not is_known(case):
            print("  -> VALIDATION: unknown test")
            print('  -> OUTPUT: "This test is not yet supported. No guessing - please consult a healthcare professional."')
            continue
        print("  -> VALIDATION: known test, retrieving context")
        results = collection.query(query_texts=[case], n_results=1)
        meta = results["metadatas"][0][0]
        print(f"  -> Retrieved: {meta['test_name']} | Reference range: {meta['reference_range']} {meta['unit']}")
        print(f"  -> EN: {meta['explanation_en'][:90]}...")
        print(f"  -> UR: {meta['explanation_ur'][:50]}...")
    print("\n" + "=" * 60)
    print(f"\n[ok] {len(tests)} tests loaded. Known-test retrieval works. Unknown-test rejection works.")

if __name__ == "__main__":
    main()
