# Day 7 — Safety Test Report

## Automated results (verified in this session — 16/16 pass)

Run `python scripts/test_safety_scenarios.py` yourself to reproduce.

| # | Scenario | Result |
|---|---|---|
| 1 | Known test, normal value → correct classification | ✅ PASS |
| 2 | Known test, abnormal value → flagged correctly (low + high) | ✅ PASS |
| 3 | Unknown test → not in alias index, never reaches retrieval | ✅ PASS |
| 4 | No diagnostic-claim language (24 lab tests + 14 medicines scanned) | ✅ PASS |
| 5 | Medicine not in database → correctly unsupported | ✅ PASS |
| 6 | Medicine present (brand, generic, alt-name) → correctly resolved | ✅ PASS |
| 7 | Multiple values in one report → all parsed and classified independently | ✅ PASS |
| 8 | Mixed known+unknown in one report → each handled correctly, independently | ✅ PASS |
| 10 | Blank/garbage OCR text → zero entries, no crash, no false match | ✅ PASS |

## Fixed during Day 7

**Scenario 12 (all-normal report → summary message)** was missing — each
test showed its own status individually, but there was no overall "all
normal" summary. Added a deterministic (non-LLM) banner: when every
recognized result in the response is `"normal"`, the frontend now shows
*"All N recognized results are within the normal reference range."*
Computed client-side from data already in the response — no new backend
logic, no new failure surface.

## Needs YOUR verification (real embeddings / real OCR / visual judgment — can't run in this sandbox)

| # | Scenario | How to test |
|---|---|---|
| 1–3, 7–8 | Same as above, but through the REAL `/analyze` endpoint (real ChromaDB retrieval, not just the alias/logic layer) | Use the manual test values from earlier in this conversation (Hemoglobin, Creatinine, MRI Brain, etc.) via the UI |
| 9 | Poor quality/blurry image → OCR extracts partial/wrong data, but manual review lets you correct it before analysis | Take a deliberately blurry or tilted photo of a report, upload it, confirm the review step lets you fix bad extractions |
| 10 (real) | Truly blank/irrelevant image (e.g. a photo of a wall) uploaded through the real OCR pipeline | Upload a random non-report photo, confirm no crash and a sensible empty/low state |
| 11 | Bilingual consistency — does the Urdu text actually convey the same meaning as the English, to a native reader? | This needs your (or an Urdu speaker's) judgment — I wrote both, but a fluent-speaker review is the real check |
| 12 (real) | Upload/enter a report where every value is genuinely normal, confirm the new banner appears | Try: Hemoglobin 14.5, LDL 80, TSH 2.0 — all within range |

## Summary

**9 of 12 scenarios are fully automated-verified.** The remaining 3 (image
quality judgment, bilingual fluency judgment, and confirming the real
ChromaDB path matches the logic-only tests) need a human — specifically
you, or ideally a native Urdu speaker for #11 — because they're not things
code can self-certify.

**Recommendation:** run through the "needs your verification" table now,
before Day 8. If anything fails, we still have a day of buffer to fix it
rather than finding out during the demo.
