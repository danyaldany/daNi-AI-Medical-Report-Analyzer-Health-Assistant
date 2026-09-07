# Day 1 — Environment & Data Foundation

## Kya ban chuka hai

1. **`data/knowledge_base.json`** — 24 verified lab tests (CBC, blood sugar, lipid profile, LFTs, KFTs), har test ke saath: unit, reference range, aur bilingual (English + Urdu) plain-language explanation.

2. **`scripts/build_knowledge_base.py`** — Production ingestion script. `sentence-transformers` (all-MiniLM-L6-v2) se knowledge base ko ChromaDB mein embed karta hai — yeh locked tech stack (Step 5) hai, same as Gov Assistant project.

3. **`scripts/query_test.py`** — Production query/validation script. Known test ko retrieve karta hai; unknown test ko deterministically reject karta hai ("not supported" — Step 4 ka safety branch).

4. **`scripts/_sandbox_validate.py`** — Sirf verification ke liye. Is sandbox mein na sentence-transformers (disk space) na ChromaDB ka default ONNX model (network restriction) download ho saka, isliye maine ek local TF-IDF substitute se **pipeline logic verify** kiya. Yeh confirm karta hai ke:
   - Known test → correct retrieval + reference range + bilingual explanation ✅
   - Unknown test (test kiya: "Troponin I") → correctly "not supported", koi hallucination nahi ✅

**Aapke actual machine pe** (jahan normal internet aur disk space available hai), `build_knowledge_base.py` aur `query_test.py` seedha chalenge — `_sandbox_validate.py` ki zaroorat nahi.

## Kaise chalayen (aapke machine pe)

```bash
cd backend
pip install -r requirements.txt
python scripts/build_knowledge_base.py   # ek baar knowledge base build karne ke liye
python scripts/query_test.py             # verify karne ke liye ke retrieval sahi kaam kar raha hai
```

## Day 1 Checkpoint — Status

- [x] Dev environment structure ready
- [x] Knowledge base data collected (24 tests, verified reference ranges, bilingual)
- [x] Ingestion pipeline code written (sentence-transformers + ChromaDB)
- [x] Retrieval + known/unknown validation logic verified (via sandbox substitute — confirm again on your real machine as a final check)
- [ ] Alibaba Cloud OCR aur Model Studio access — yeh aapko khud confirm karna hoga (API keys, account setup) — main yeh nahi kar sakta

## Agla step — Day 2

Medicine info dataset assemble karna (WHO/NIH + Pakistan-relevant source — abhi tak finalize nahi hua, yeh pehle decide karna hoga) aur data validation logic ko backend mein wire karna.
