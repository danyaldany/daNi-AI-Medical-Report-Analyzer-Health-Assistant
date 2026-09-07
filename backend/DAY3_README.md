# Day 3 — Input Pipeline (Upload + OCR + Mandatory Manual Review)

## Kya ban chuka hai

1. **`backend/app/ocr.py`** — Alibaba Cloud OCR integration (Component 2). **Important:** mujhe Alibaba Cloud credentials access nahi hai, isliye real API call **live test nahi ki ja saki** — code current documentation ke mutabiq likha hai, lekin aapko apne credentials ke saath verify karna hoga (endpoint/response field names Alibaba Cloud ki current docs se match karo). Credentials na hone par yeh automatically **MOCK mode** mein chalta hai (ek sample report ka text return karta hai) — taake baaki pipeline build/test ho sake.

2. **`backend/app/report_parser.py`** — Raw OCR text ko structured entries (test name, value, unit) mein todta hai. Regex-based, deterministic — LLM use nahi kiya isme, kyunke parsing ek rule-based kaam hai aur ismein LLM lagana hallucination risk add karta hai.

3. **`backend/app/main.py`** — Naya endpoint `POST /ocr/extract` add hua, CORS bhi enable hua (frontend se connect karne ke liye).

4. **`frontend/`** — Poora Next.js app (naya). `app/page.tsx` mein:
   - File upload
   - **Mandatory manual review table** — extracted values hamesha edit karne ke liye dikhti hain (Step 7 ka locked decision — koi confidence-check skip logic nahi)
   - "Confirm and analyze" button jo `/analyze` ko call karta hai
   - Results bilingual (English + Urdu) display hote hain, "not supported" cases bhi properly dikhte hain
   - Disclaimer line neeche

**Verified in this sandbox:**
- `/ocr/extract` endpoint (mock mode) — 4 test entries correctly parse hui ✅
- Frontend `npm run build` — 0 errors, successfully compile hua ✅

**Aapke machine pe verify karna hai:**
- `/analyze` endpoint (sandbox mein knowledge base collection nahi thi is baar, lekin Day 2 mein already verify ho chuka tha)
- Real Alibaba Cloud OCR call (credentials chahiye)
- Frontend + backend end-to-end (dono ek saath chala ke)

## Kaise chalayen (aapke machine pe)

**Terminal 1 — backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 — frontend:**
```bash
cd frontend
npm install
npm run dev
```

Phir browser mein `http://localhost:3000` kholo, ek report image upload karo (ya bina Alibaba credentials ke bhi try karo — mock mode se sample data aayega), extracted values check/edit karo, "Confirm and analyze" dabao.

## Alibaba Cloud OCR real credentials wire karne ke liye

`.env` file (ya environment variables) mein set karo:
```
ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret
```

Phir `backend/app/ocr.py` ke "Real Alibaba Cloud OCR call" section ko unki current documentation ke against verify/adjust karo — maine jo likha hai woh structurally sahi hai lekin live test nahi ho saka.

## Day 3 Checkpoint — Status

- [x] Upload UI
- [x] OCR integration code (mock-verified; real API — verify with your credentials)
- [x] Parser (verified with mock data)
- [x] Mandatory manual review form (frontend build verified)
- [ ] Real OCR credentials ke saath end-to-end test — aapko karna hai

## Agla step — Day 4

Explanation generation (Component 5): LLM prompting, bilingual output, abnormal-value flagging, safety filter, "doctor se kya poochein" suggestions.
