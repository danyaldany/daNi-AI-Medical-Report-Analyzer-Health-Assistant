
---

## 📄 File 3: `DAY3_Input_Pipeline_Upload_OCR_Review.md`

```markdown
# Day 3 — Input Pipeline (Upload + OCR + Mandatory Manual Review)

## Kya ban chuka hai

1. **`backend/app/ocr.py`** — Multi-layer OCR pipeline:
   - **Primary:** Gemini Vision (structured extraction, reads typed + handwritten)
   - **Fallback 1:** Alibaba Cloud OCR
   - **Fallback 2:** Tesseract (local, offline)
   - **Fallback 3:** Mock data (development mode)

2. **`backend/app/vision_extract.py`** — Gemini Vision structured extraction. Extract karta hai: test_name, value, unit, normal_range, category. **Qualitative tests** ke liye bhi kaam karta hai.

3. **`backend/app/report_parser.py`** — Raw OCR text ko structured entries (test name, value, unit) mein todta hai. Regex-based, deterministic — LLM use nahi kiya.

4. **`backend/app/main.py`** — Naya endpoint `POST /ocr/extract` add hua, CORS enable hua.

5. **`frontend/`** — Poora Next.js app:
   - File upload (drag & drop)
   - **Mandatory manual review table** — extracted values hamesha edit karne ke liye dikhti hain
   - Category tabs: Bio-Chemistry, Serology, Hematology
   - Medicines section (optional)
   - "Confirm and analyze" button
   - Results display with bilingual explanations, charts, and doctor questions

## Kaise chalayen (aapke machine pe)

**Terminal 1 — backend:**
```bash
cd backend
uvicorn app.main:app --reload


Terminal 2 — frontend:

bash
cd frontend
npm install
npm run dev
Phir browser mein http://localhost:3000 kholo.

Alibaba Cloud / Gemini Credentials
.env file mein set karo:

text
GEMINI_API_KEY=your_gemini_api_key
ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret
