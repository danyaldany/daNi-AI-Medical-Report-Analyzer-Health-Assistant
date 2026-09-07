# Pitch Structure — Regional Round

**Target: 4–5 minutes total (adjust to actual time slot given).**

---

## 1. Problem (30 seconds)

Patients across Pakistan receive lab reports full of English medical
terminology and numbers they can't interpret. Most are more comfortable in
Urdu. Doctor consultation time is short, and patients often leave without
understanding what their results mean or what to ask next.

*(Optional: mention this personally — you built this after seeing this
exact gap.)*

---

## 2. Solution (30 seconds)

**Sehat Samjho** — an AI Medical Report Analyzer that turns a photographed
lab report into a clear, bilingual (Urdu + English) explanation: what each
result means, whether it's normal, and what to ask your doctor. Built
safety-first: it never guesses, never diagnoses.

---

## 3. Live Demo (2–3 minutes)

Follow `DAY8_Demo_Script.md` — Scenarios 1–4 minimum, Scenario 5 if time allows.

**Narrate while it runs — don't demo in silence.** Judges follow the story better with commentary.

---

## 4. Technical Approach (45 seconds)

- **RAG-grounded, not open generation:** ChromaDB + sentence-transformers retrieve only from a verified ~24-test knowledge base — no hallucination risk from unbounded generation
- **Alibaba Cloud integration:** OCR API for report extraction (with a resilient local fallback), and Model Studio for LLM-enhanced, personalized bilingual explanations — always with a safe static fallback if either service is unavailable
- **Deterministic safety layer:** abnormal-value flagging and known/unknown test classification are rule-based, not AI-guessed — the AI only touches what's already verified safe

---

## 5. Safety & Responsible AI (30 seconds)

*This is a genuine differentiator — spend real time here, judges notice it.*

- Every explanation carries a clear "consult a doctor" disclaimer
- No diagnostic language anywhere in the system (verified via automated scan of all 24 test + 14 medicine entries)
- Unknown tests/medicines get an explicit "not supported" response — never a guess
- 16 automated safety tests + structured manual test scenarios, documented and passing

---

## 6. Impact (20 seconds)

Designed for real Pakistani patients — tested against an actual local lab
report (Al-Shifa Medical Laboratory, Swabi), not a synthetic example.
Scalable to any patient with a smartphone camera, no app install required.

---

## 7. What's Next (15 seconds, only if asked or time remains)

- Expand the verified test/medicine knowledge base
- Prescription and imaging report support
- Deeper Alibaba Cloud Model Studio integration for follow-up conversational Q&A

---

## Anticipated Judge Questions — be ready

| Question | Answer |
|---|---|
| "How do you prevent wrong medical advice?" | Hard known/unknown gate before any generation; no diagnostic language anywhere; disclaimer on every result. Point to the 16 automated tests. |
| "Why not just use a bigger LLM for everything?" | Deliberate choice — RAG-bounded retrieval eliminates hallucination risk that a fully open LLM call would introduce, which matters more in healthcare than broader coverage. |
| "What if Alibaba OCR is down?" | Automatic local Tesseract fallback, then manual entry — demonstrated live if needed. |
| "Is this real data?" | Yes — tested against an actual patient's real lab report, not synthetic examples only. |
| "How is this different from just asking ChatGPT?" | No memory of what's verified vs. not, no retrieval grounding, no deterministic safety gate — a general chatbot can hallucinate a reference range or a diagnosis. This system structurally cannot. |
