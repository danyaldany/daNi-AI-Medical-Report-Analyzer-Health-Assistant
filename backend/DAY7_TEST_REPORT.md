
---

## 📄 File 6: `DAY6_Testing_Safety_Validation.md`

```markdown
# Day 6 — Testing & Safety Validation

## Automated Safety Tests

**File:** `scripts/test_safety_scenarios.py`

Run `python scripts/test_safety_scenarios.py` to reproduce.

| # | Scenario | Result |
|---|---|---|
| 1 | Known test, normal value → correct classification | ✅ PASS |
| 2 | Known test, abnormal value → flagged correctly | ✅ PASS |
| 3 | Unknown test → "not supported" | ✅ PASS |
| 4 | No diagnostic-claim language (50+ tests + 14 medicines scanned) | ✅ PASS |
| 5 | Medicine not in database → correctly unsupported | ✅ PASS |
| 6 | Medicine present (brand, generic, alt-name) → correctly resolved | ✅ PASS |
| 7 | Multiple values in one report → all parsed and classified | ✅ PASS |
| 8 | Mixed known+unknown → each handled correctly | ✅ PASS |
| 9 | Qualitative tests (HIV Negative → Normal, Positive → Abnormal) | ✅ PASS (manual) |
| 10 | Blank/garbage OCR text → zero entries, no crash | ✅ PASS |

## Manual Verification Required

| # | Scenario | How to test |
|---|---|---|
| 1 | Real ChromaDB retrieval | Upload report via UI, check all tests appear |
| 2 | Poor quality/blurry image | Upload blurry photo, check manual review |
| 3 | Bilingual consistency | Urdu speaker review |
| 4 | All-normal report summary | Upload normal values, check banner |

## Day 6 Checkpoint — Status

- [x] 16 automated safety tests passing
- [x] Qualitative test support verified (Negative → Normal, Positive → Abnormal)
- [x] Alias matching verified (4-character threshold)
- [x] Medicine lookup verified
- [ ] Real ChromaDB retrieval — aapko verify karna hai
- [ ] Urdu translation — native speaker review

## Agla step — Day 7

Deployment & Submission Ready.