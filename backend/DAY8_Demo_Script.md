# Demo Script — Regional Round / Judge Presentation

Verified working data, tested end-to-end during build. Use these exact
values so the demo is predictable and rehearsed — no live surprises.

**Total time target: 2–3 minutes for the full demo.**

---

## Scenario 1 — Real report upload (the "wow" moment)

**Use:** Your actual Al-Shifa lab report photo (the clear one, well-lit, taken from above).

1. Upload the image
2. Point out: OCR runs (Alibaba Cloud primary → automatic Tesseract fallback if needed — mention this shows engineering resilience, not just a single point of failure)
3. **Manual review screen appears** — say clearly: *"The system never assumes — every extracted value is shown for confirmation before we analyze anything."*
4. A few test names are pre-filled (from name-recognition); confirm/add Hemoglobin: 10.8, Creatinine: 0.8
5. Click "Confirm and analyze"

**What this demonstrates:** real OCR, safety-first manual confirmation, resilience (dual OCR).

---

## Scenario 2 — Abnormal value + bilingual LLM explanation

**Data:** Hemoglobin = 10.8 (already entered from Scenario 1)

**Point out on screen:**
- Reference range shown clearly
- "Outside reference range" flag — deterministic, not AI-guessed
- Explanation is personalized (mentions the actual value 10.8) — generated via **Alibaba-approach LLM enhancement, with automatic fallback to verified static text if the LLM is unavailable** (say this explicitly — it shows you engineered for reliability)
- Full Urdu translation alongside English
- "Questions to ask your doctor" — practical, not just informational

---

## Scenario 3 — Unknown test → safety in action

**Data:** Type a test manually — e.g. **"MRI Brain"**

**Say:** *"Healthcare AI can't guess. Watch what happens when we ask about something outside our verified knowledge base."*

**Result:** "This test is not yet supported. No guessing — please consult a healthcare professional about this result."

**What this demonstrates:** the system has a hard safety boundary — it does not hallucinate medical information for tests it hasn't verified.

---

## Scenario 4 — Medicine lookup

**Data:** Add medicine **"Panadol"**

**Result:** Generic name (Paracetamol), Pakistan brand names, purpose, safety notes — bilingual.

**Then add:** **"RandomDrug123"** → correctly "not supported" — reinforce the safety point once more, quickly.

---

## Scenario 5 (if time allows) — All-normal summary

**Data:** LDL Cholesterol = 85, TSH = 2.1 (both within range)

**Result:** Green summary banner: *"All 2 recognized results are within the normal reference range."*

**What this demonstrates:** the system doesn't just flag problems — it gives clear reassurance when everything is fine, which is equally valuable for patients.

---

## If OCR fails live (Alibaba service not activated, or network issue)

**Do not panic — say this directly, confidently:**

> "If Alibaba OCR isn't available right now, the system automatically falls back to a local OCR engine, and if that also can't read a value, you simply confirm it manually — the system never crashes and never blocks you from getting your results explained."

Then proceed with manual entry for Scenario 2 onward. **This is not a failure — it's the safety design working as intended.** Frame it that way.
