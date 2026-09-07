# Day 2 — Medicine Info + FastAPI Backend Wiring

## Kya ban chuka hai

1. **`data/medicine_info.json`** — 14 common medicines (Pakistan brand names + generic names), general purpose aur safety notes (bilingual). **Important:** yeh ek starter set hai MVP demo ke liye — koi finalized/authoritative dataset nahi. Regional round se pehle isko expand/verify karna chahiye, ideally kisi pharmacology background wale se review karwa ke.

2. **`app/knowledge.py`** — Component 3 (validation) + Component 4 (RAG retrieval) ka reusable module — `query_test.py` ki logic yahan refactor hui hai taake CLI script aur API dono same code use karein.

3. **`app/medicine.py`** — Component 6 (Medicine Lookup), independent module. Isi mein **ek bug mila aur fix kiya**:
   - **Bug:** `"paracetamol"` search karne pe "not supported" aa raha tha, kyunki knowledge base mein generic name `"Paracetamol (Acetaminophen)"` poora string store tha — exact match fail ho raha tha.
   - **Fix:** `query_test.py` wala hi alias-splitting pattern yahan bhi apply kiya — ab short name aur bracket ke andar wala alternate name dono se match hota hai.
   - Verify kiya: `Panadol`, `paracetamol`, `Acetaminophen` — teeno ab `Paracetamol (Acetaminophen)` ko correctly match karte hain.

4. **`app/main.py`** — FastAPI app, 4 endpoints:
   - `GET /health` — service check
   - `GET /test/{test_name}` — single lab test lookup (sentence-transformers chahiye — aapke machine pe test karo)
   - `GET /medicine/{medicine_name}` — single medicine lookup (**verified working** ✅)
   - `POST /analyze` — combined endpoint, tests + medicines dono ek request mein

**Note:** Explanation generation (Component 5, LLM step) abhi wire nahi hua — yeh Day 4 ka kaam hai. Abhi API sirf validation + retrieval prove karta hai.

## Kaise chalayen (aapke machine pe)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Phir browser mein `http://127.0.0.1:8000/docs` khol ke interactively test karo:
- `/medicine/Panadol` → medicine info aana chahiye
- `/test/Hemoglobin` → lab test info aana chahiye
- `/test/Troponin` → "not supported" aana chahiye
- `/medicine/RandomDrug` → "not supported" aana chahiye

## Day 2 Checkpoint — Status

- [x] Medicine info dataset (14 medicines, starter set — flagged as not yet finalized)
- [x] Validation + retrieval logic refactored into reusable modules
- [x] Medicine lookup bug found aur fixed (alias matching)
- [x] FastAPI endpoints built aur medicine endpoint verified working
- [ ] `/test/{test_name}` endpoint — aapke machine pe verify karna hai (sentence-transformers chahiye)
- [ ] `/analyze` combined endpoint — aapke machine pe end-to-end test karo

## Agla step — Day 3

Input pipeline: upload UI + Alibaba Cloud OCR integration + mandatory manual-confirmation step (Component 1-3).
