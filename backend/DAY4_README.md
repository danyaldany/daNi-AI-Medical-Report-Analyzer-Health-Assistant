
---

## 📄 File 4: `DAY4_Explanation_Generation.md`

```markdown
# Day 4 — Explanation Generation (Component 5)

## Kya bana

1. **`backend/app/abnormal_check.py`** — Deterministic abnormal-value flagging.
   - `check_abnormal()` — numeric ranges (e.g., "13.5-17.5")
   - `check_qualitative()` — Positive/Negative tests (HIV, HBsAg, etc.)
   - Gender-split ranges handle hoti hain (combined bound)
   - Multi-tier ranges (HbA1c) → "range_unclear" — guess nahi karta

2. **`backend/app/doctor_questions.py`** — "Doctor se kya poochein" suggestions. Category + abnormal-status based templates. **LLM se nahi bana** — deterministic.

3. **`backend/app/llm_generation.py`** — LLM explanation enhancement.
   - **Gemini Flash** primary (contextual 4-5 sentence explanations)
   - **Static fallback** if LLM unavailable or fails
   - Bilingual output (English + Urdu)
   - Strict safety rules — no diagnosis, always "may indicate"

4. **`backend/app/knowledge.py`** — Integrated abnormal status, doctor questions, aur LLM explanation.

5. **Frontend** — Abnormal status badge (green/red/amber) aur doctor questions display.

## Safety Check

- **24+ explanations scanned** — koi diagnostic-claim language nahi mili
- **Qualitative tests** — "Negative" → Normal, "Positive" → Abnormal
- **Static fallback** — always available, never breaks

## Kaise test karo (aapke machine pe)

```bash
cd backend
python scripts/build_knowledge_base.py  # agar pehle se nahi bana
uvicorn app.main:app --reload

/docs se /analyze try karo:

json
{
  "tests": [
    {"test_name": "Hemoglobin", "value": "10.6"},
    {"test_name": "HIV", "value": "Negative"},
    {"test_name": "Creatinine", "value": "0.8"}
  ],
  "medicines": ["Panadol"]
}