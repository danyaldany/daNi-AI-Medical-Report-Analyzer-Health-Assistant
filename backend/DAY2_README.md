
---

## 📄 File 2: `DAY2_Medicine_Info_FastAPI_Wiring.md`

```markdown
# Day 2 — Medicine Info + FastAPI Backend Wiring

## Kya ban chuka hai

1. **`data/medicine_info.json`** — 14 common medicines (Pakistan brand names + generic names), general purpose aur safety notes (bilingual). Starter set hai — expand kiya ja sakta hai.

2. **`app/knowledge.py`** — Component 3 (validation) + Component 4 (RAG retrieval) ka reusable module. Alias matching ab **4-character threshold** use karta hai (5 se 4 kiya taake "SGPT" match ho, "Hb" jaise 2-character aliases false-positive na dein).

3. **`app/medicine.py`** — Component 6 (Medicine Lookup), independent module. Alias-splitting pattern apply hai — "Panadol", "paracetamol", "Acetaminophen" teeno "Paracetamol (Acetaminophen)" ko correctly match karte hain.

4. **`app/main.py`** — FastAPI app, 4 endpoints:
   - `GET /health` — service check
   - `GET /test/{test_name}` — single lab test lookup
   - `GET /medicine/{medicine_name}` — single medicine lookup
   - `POST /analyze` — combined endpoint, tests + medicines dono ek request mein

## Kaise chalayen (aapke machine pe)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

Phir browser mein http://127.0.0.1:8000/docs khol ke interactively test karo:

/medicine/Panadol → medicine info aana chahiye

/test/Hemoglobin → lab test info aana chahiye

/test/Troponin → "not supported" aana chahiye

/medicine/RandomDrug → "not supported" aana chahiye