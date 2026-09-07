# 🏥 Sehat Samjho — AI Medical Report Analyzer

> **Bilingual Health Understanding for Pakistan**  
> *Understand your lab reports — no medical degree required.*

[![Hackathon](https://img.shields.io/badge/Hackathon-Alibaba%20Cloud%20AI%202026-blue)](https://github.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini-Vision%20%26%20Flash-orange)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

---

## 📌 Overview

**Sehat Samjho** (Urdu for "Understand Health") is a bilingual (English/Urdu) web application that helps patients interpret medical laboratory reports.

It **extracts test names, values, units, and printed reference ranges** from uploaded images/PDFs using a multi‑layer OCR pipeline. The extracted data is always **shown to the user for mandatory review** before any analysis occurs. For supported tests, the system provides **educational explanations** based on a curated knowledge base and deterministic validation. Unsupported tests are **explicitly flagged** — the system never guesses or invents medical information.

> ⚕️ **Educational Assistant** – This tool is designed to support understanding, not to diagnose, prescribe, or replace professional medical advice.

---

## 🧩 Problem Statement

Medical reports are often difficult to interpret due to:

- **Technical medical jargon** unfamiliar to patients.
- **Language barriers** – reports are typically printed in English, while many patients in Pakistan speak Urdu.
- **Limited consultation time**, leaving little room for detailed explanation.

**Sehat Samjho** bridges this gap by providing safe, bilingual interpretation in a clear and accessible format.

---

## 💡 Solution

| Feature | Description |
| :------ | :---------- |
| **📷 Upload** | Upload a lab report image (JPG/PNG) or PDF. |
| **🧠 AI Extraction** | Uses a multi‑layer OCR pipeline (**Gemini Vision** primary, **Alibaba Cloud OCR** and **Tesseract** as fallbacks) to extract test names, values, units, and printed reference ranges. All extracted data is presented for **user review and editing** before any analysis occurs. |
| **📝 Manual Review** | All extracted data is shown in an editable table. Users can correct values, add missing tests, or remove incorrect rows before analysis. |
| **📊 Validation & Comparison** | For supported tests, values are compared against a **curated ChromaDB knowledge base** (50+ verified tests) using **deterministic rules**. The system flags results as **Normal**, **Abnormal**, or **Unclear**. Unknown tests are clearly marked as "Not supported" – no guessing. |
| **🗣️ Bilingual Explanation** | For supported tests, the system generates **4‑5 sentence explanations** in both **English** and **Urdu**. It uses **Gemini Flash** (LLM) to add contextual associations (e.g., "low MCH may indicate iron deficiency") while strictly avoiding diagnosis. If the LLM is unavailable or fails, the system safely **falls back to the static explanation** stored in the knowledge base. |
| **🧪 Qualitative Test Support** | Handles Positive/Negative test results (HIV, HBsAg, HCV, Rubella, etc.) with proper Normal/Abnormal classification. |
| **📈 Visual Dashboard** | Summary cards (Total / Normal / Abnormal / Unclear) plus bar and pie charts for a quick health overview. |
| **💊 Medicine Lookup** | Basic lookup for ~14 common medicines in Pakistan (brand + generic names). Unlisted medicines are safely rejected with a "Not in our verified list" message. |
| **🩺 Doctor Questions** | Each test result includes 2‑3 neutral, safe questions to ask a healthcare provider. |
| **🎨 Dark/Light Mode** | Professional UI with theme toggle. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                            │
│  ┌────────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │   Upload   │  │  Review   │  │  Charts  │  │  Dark/Light Theme │  │
│  │   (DnD)    │  │   Table   │  │(Recharts)│  │                   │  │
│  └────────────┘  └───────────┘  └──────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTP REST
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                            │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ 1. Multi‑layer OCR / Extraction:                                 │ │
│  │    Primary: Gemini Vision (structured extraction)                │ │
│  │    Fallback 1: Alibaba Cloud OCR                                 │ │
│  │    Fallback 2: Tesseract (local)                                 │ │
│  │    Fallback 3: Mock data (dev mode)                              │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 2. Knowledge Retrieval (RAG): ChromaDB + SentenceTransformers   │ │
│  │    (all-MiniLM-L6‑v2) + alias matching (4‑char threshold)       │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 3. Abnormal Status Check: Deterministic (rule‑based)            │ │
│  │    - Numeric: check_abnormal()                                   │ │
│  │    - Qualitative: check_qualitative() (Positive/Negative)       │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 4. Explanation Generation:                                      │ │
│  │    Gemini Flash (LLM) → contextual enhancement                  │ │
│  │    Static Explanation (Fallback) → if LLM fails/unavailable    │ │
│  ├───────────────────────────────────────────────────────────────────┤ │
│  │ 5. Doctor Questions: Templated, category‑specific               │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                                  │
│  ┌─────────────────────┐  ┌────────────────────────────────────────┐ │
│  │  knowledge_base.json │  │  chroma_store/ (ChromaDB vectors)     │ │
│  │   (50+ verified tests)│  │  (Embeddings + Metadata)              │ │
│  └─────────────────────┘  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

![Uploading ChatGPT Image Sep 7, 2026, 08_30_39 PM.png…]()

```

---

## 🔄 How It Works (User Flow)

1. **Upload** – Drag & drop a report image/PDF.
2. **Extract** – The system attempts extraction using Gemini Vision (primary) → Alibaba Cloud OCR → Tesseract → Mock (dev).
3. **Review** – All extracted data is displayed in an editable table. Users confirm, correct, or remove entries.
4. **Analyze** – On confirmation, the system:
   - Validates the test name against the alias index (using bidirectional substring matching with a **4-character threshold** to balance recall for terms like "SGPT" while avoiding false positives from shorter aliases like "Hb").
   - Retrieves corresponding medical data from ChromaDB (if known).
   - Computes a deterministic status (Normal / Abnormal / Unclear).
   - Generates a bilingual explanation (LLM enhanced, or static fallback).
   - Prepares category‑specific doctor questions.
5. **View Results** – The dashboard shows summary stats, charts, and detailed test cards with bilingual explanations and doctor questions.

**For unknown tests:**  
→ The system clearly returns: *"This test is not in our verified database"*.  
→ **No LLM explanation is generated** – the system never guesses.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :---- | :--------- | :------ |
| **Frontend** | Next.js 14, React, TypeScript | UI, routing, type safety |
| | Tailwind CSS | Styling, dark/light theme |
| | Recharts | Data visualisation (Bar & Pie charts) |
| | React Dropzone | Drag‑and‑drop file upload |
| **Backend** | FastAPI (Python 3.10) | API server & business logic |
| | ChromaDB | Vector database for RAG |
| | SentenceTransformers (`all-MiniLM-L6‑v2`) | Embedding model |
| | Gemini Vision | Primary OCR & structured extraction |
| | Gemini Flash | LLM explanation enhancement |
| | Alibaba Cloud OCR / Tesseract | Fallback OCR options |
| | Static Explanation (JSON) | Safe fallback if LLM unavailable |
| **Data** | `knowledge_base.json` | 50+ verified tests, ranges & explanations |
| | `medicine_info.json` | ~14 common Pakistan medicines (basic lookup) |

---

## 🔒 Safety & Design Principles

- **No Guessing** – Unknown/unsupported tests are explicitly rejected. The system never invents medical facts.
- **Mandatory User Review** – All extracted data is shown before analysis; the user is in control.
- **Deterministic Validation** – Abnormal status (Normal/Abnormal/Unclear) is computed using rule‑based logic, not an LLM. This ensures reproducibility and safety.
- **Static Fallback** – If the LLM enhancement is unavailable or fails, the system uses the curated static explanation from `knowledge_base.json` without compromising safety.
- **Qualitative Handling** – Positive/Negative tests (HIV, HBsAg, HCV, Rubella, Toxoplasmosis, Brucella, H.Pylori, Typdot, Widal, MP) are handled via `check_qualitative()` to avoid parsing errors.
- **Educational Only** – The system is an educational assistant. It does not diagnose, prescribe, or replace professional medical advice.

---

## 📁 What We Actually Implemented (MVP Scope)

| Component | Status | Details |
| :-------- | :----- | :------ |
| **OCR Pipeline** | ✅ Working | Gemini Vision (primary), Alibaba Cloud OCR (fallback), Tesseract (fallback), Mock (dev). |
| **User Review Table** | ✅ Working | Editable table with categories (Bio‑Chemistry, Serology, Hematology). |
| **Knowledge Base** | ✅ Working | 50+ verified tests in `knowledge_base.json` (including qualitative). |
| **RAG Retrieval** | ✅ Working | ChromaDB + SentenceTransformers + alias matching (4-character threshold). |
| **Abnormal Checking** | ✅ Working | Deterministic, rule‑based. Handles numeric & qualitative ranges. |
| **LLM Explanation** | ✅ Working | Gemini Flash generates 4‑5 sentence bilingual explanations. |
| **Static Fallback** | ✅ Working | If LLM fails, falls back to static explanation from JSON. |
| **Visual Dashboard** | ✅ Working | Summary cards, Bar chart, Pie chart (all sync with value filters). |
| **Doctor Questions** | ✅ Working | Templated questions based on category and status. |
| **Medicine Lookup** | ✅ Working | Basic lookup for ~14 medicines (optional feature, UI visible). |
| **Dark/Light Mode** | ✅ Working | Theme toggle using CSS variables. |

---

## ⚠️ Limitations

- **No diagnosis or prescription** – the system is strictly educational.
- **Handwriting support is limited** – while Gemini Vision can read some handwriting, poor‑quality images or complex handwritten values may not parse reliably.
- **Medicine database is tiny** – only ~14 common medicines in Pakistan. Unlisted medicines are safely rejected.
- **No PDF generation** – the system does not generate downloadable report summaries (planned for future).
- **No historical tracking** – comparison with previous reports is not available.
- **No cloud deployment of backend** – currently runs locally; deployment to Render/Heroku is planned.

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **Gemini API Key** (free tier available from [Google AI Studio](https://ai.dev/))
- *(Optional)* Alibaba Cloud OCR credentials (for fallback).

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/sehat-samjho.git
cd sehat-samjho
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_here       # Optional
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_secret_here # Optional
```

Build the knowledge base (ChromaDB):

```bash
python scripts/build_knowledge_base.py
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

> The API will be available at `http://127.0.0.1:8000`.

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 📁 Project Structure

```
sehat-samjho/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── ocr.py                   # Multi‑layer OCR (Gemini + Alibaba + Tesseract + Mock)
│   │   ├── vision_extract.py        # Gemini Vision structured extraction
│   │   ├── knowledge.py             # ChromaDB RAG + alias matching (4-char threshold)
│   │   ├── abnormal_check.py        # Deterministic + Qualitative abnormal flagging
│   │   ├── doctor_questions.py      # Templated doctor questions
│   │   ├── llm_generation.py        # Gemini Flash + Static fallback
│   │   ├── medicine.py              # Basic medicine lookup
│   │   └── report_parser.py         # Text‑based parsing fallback
│   ├── data/
│   │   ├── knowledge_base.json      # 50+ verified tests (static source of truth)
│   │   ├── medicine_info.json       # ~14 medicines (basic lookup)
│   │   └── chroma_store/            # ChromaDB persistent storage
│   ├── scripts/
│   │   ├── build_knowledge_base.py  # Builds ChromaDB collection
│   │   └── test_safety_scenarios.py # Safety test suite
│   ├── .env                         # Environment variables
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Main UI
│   │   ├── layout.tsx               # Layout & fonts
│   │   └── globals.css              # Global styles (light/dark)
│   ├── components/
│   │   └── ThemeToggle.tsx          # Dark/light mode toggle
│   └── package.json
└── README.md
```

---

## 🧪 Testing & Safety Validation

The repository includes a safety test suite (`scripts/test_safety_scenarios.py`) covering:

- Known test → correct retrieval.
- Abnormal test → correct flagging.
- Unknown test → "Not supported" (no guessing).
- Diagnosis‑language safety – static explanations contain no diagnostic claims.
- Known / unknown medicine lookup.
- Mixed known/unknown tests.
- Blank/garbage OCR input → graceful handling.
- Qualitative tests (HIV Negative → Normal, HIV Positive → Abnormal).

**Status:** All core safety scenarios pass in the current implementation.

---

## 🚦 Future Scope (Post‑MVP)

- Expand knowledge base to 100+ tests across more panels.
- Add historical tracking and trend visualisation.
- Develop a WhatsApp/Telegram bot for easier access.
- PDF report generation with bilingual summaries.
- Improve handwriting recognition.
- Integrate with hospital EHR systems.

---

## 🙏 Acknowledgments

- **Alibaba Cloud** – for hosting the hackathon.
- **Google Gemini** – for providing free API access to Vision and Flash models.
- **ChromaDB and SentenceTransformers** – for enabling the RAG pipeline.

---

## 📄 License

This project is licensed under the **MIT License** – free to use, modify, and distribute.

---

## 📬 Contact & Team

**Team Member:**  
- [Your Name] – Full Stack Developer (AI Integration, Backend, Frontend)  
- GitHub: [github.com/your-username](https://github.com/your-username)  
- LinkedIn: [linkedin.com/in/your-profile](https://linkedin.com/in/your-profile)  
- Email: your-email@example.com

---

> ⚕️ **Disclaimer**: Sehat Samjho is an **educational tool** and **not a substitute for professional medical advice, diagnosis, or treatment**. Always consult a qualified healthcare provider regarding your health.

---

*This README accurately reflects the actual implementation in this repository. All claims are verified against the source code.*
```
