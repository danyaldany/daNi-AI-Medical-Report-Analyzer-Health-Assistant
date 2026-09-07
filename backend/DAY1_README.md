# Day 1 — Environment & Data Foundation

## Kya ban chuka hai

1. **`data/knowledge_base.json`** — 50+ verified lab tests (CBC, blood sugar, lipid profile, LFTs, KFTs, Serology, Hematology, Bio-Chemistry), har test ke saath: unit, reference range, bilingual (English + Urdu) plain-language explanation, aur qualitative test support (Positive/Negative).

2. **`scripts/build_knowledge_base.py`** — Production ingestion script. `sentence-transformers` (all-MiniLM-L6-v2) se knowledge base ko ChromaDB mein embed karta hai — yeh locked tech stack hai, same as Gov Assistant project.

3. **`scripts/query_test.py`** — Production query/validation script. Known test ko retrieve karta hai; unknown test ko deterministically reject karta hai ("not supported").

4. **`scripts/_sandbox_validate.py`** — Sirf verification ke liye. Local TF-IDF substitute se pipeline logic verify kiya.

## Updated Features (Day 1 Enhancements)

- **Qualitative Test Support:** HIV, HBsAg, HCV, Rubella, Toxoplasmosis, Brucella, H.Pylori, Typdot, Widal, MP — sab qualitative tests ab `is_qualitative: true`, `normal_value: "Negative"`, `abnormal_values: ["Positive", "Reactive"]` ke saath support hain.
- **Alias Fixes:** Blood Group se "Rh Factor" hata diya (sirf rh_factor mein rakha), T.C.L se "WBC" aur "White Blood Cell Count" hata diya.
- **Test Count:** 24 se 50+ tests expand ho gaye.

## Kaise chalayen (aapke machine pe)

```bash
cd backend
pip install -r requirements.txt
python scripts/build_knowledge_base.py   # ek baar knowledge base build karne ke liye
python scripts/query_test.py             # verify karne ke liye ke retrieval sahi kaam kar raha hai