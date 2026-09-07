"""
Day 2 — FastAPI backend, wiring Component 3+4 (knowledge.py) and
Component 6 (medicine.py) into API endpoints.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.knowledge import get_test_info
from app.medicine import lookup_medicine
from app.ocr import extract_text_from_image
from app.report_parser import parse_report_text, find_known_test_names
from app.knowledge import _load_alias_index, _load_category_index
from app.vision_extract import extract_tests_with_vision

app = FastAPI(title="AI Medical Report Analyzer API")

origins = [
    "https://sehat-iw9z1j1d0-da-ni1.vercel.app",  # Aapka Vercel deployment URL
    "https://sehatsamjomedical.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+",
    allow_origins=["*"],            # Allow all origins to prevent any Vercel domain mismatches
    allow_credentials=False,        # Must be False when using wildcard "*"
    allow_methods=["*"],            # Allows GET, POST, OPTIONS, PUT, DELETE
    allow_headers=["*"],            # Allows all headers (Authorization, Content-Type, etc.)
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Medical Report Analyzer API is running!"}

# app.add_middleware(
#     CORSMiddleware,
#     # Bug fix: Next.js falls back to another port (3001, 3002...) if 3000 is
#     # busy, and the previous fixed allow_origins=["http://localhost:3000"]
#     # silently blocked every other port with a browser-side "Failed to
#     # fetch" (a CORS preflight rejection, not a backend error). Allowing
#     # any localhost/127.0.0.1 port covers this for local development.
#     allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_origins=[
#         "https://sehat-iw9z1j1d0-da-ni1.vercel.app/",  # ← Apni Vercel URL daalein
#         "http://localhost:3000"],
# )


class TestResult(BaseModel):
    test_name: str
    value: Optional[str] = None
    normal_range: Optional[str] = None  # printed range from the report itself, used only for unsupported tests
    category: Optional[str] = None      # ADDED: for the categories feature


class AnalyzeRequest(BaseModel):
    tests: List[TestResult] = []
    medicines: List[str] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ocr/extract")
async def ocr_extract(file: UploadFile = File(...)):
    """
    Component 1 (User Input) + Component 2 (OCR Extraction).
    Returns extracted entries for the frontend to show in a MANDATORY
    manual-review/edit form — nothing here is treated as final. The user
    must confirm/edit before /analyze is called (Step 7's locked decision:
    always show extracted data for confirmation, no confidence threshold).
    """
    file_bytes = await file.read()

    # Vision extraction (Gemini, reads handwriting + table layout directly)
    # tried first if available -- generally more capable than text-only OCR
    # for real-world reports. Falls back to text OCR if unavailable or if
    # it returns nothing.
    vision_results = extract_tests_with_vision(file_bytes, mime_type=file.content_type or "image/jpeg")

    if vision_results:
        entries = vision_results
        raw_text = f"[Extracted via vision model — {len(entries)} value(s) found]"
    else:
        raw_text = extract_text_from_image(file_bytes, filename=file.filename)
        entries = parse_report_text(raw_text)

    # Name-only suggestions (test name recognized, but no value could be
    # read nearby -- usually because it's handwritten). Returned SEPARATELY
    # from extracted_tests now, per user feedback: auto-filling empty rows
    # into the main table created clutter (rows to delete rather than
    # rows to use). The frontend shows these as click-to-add suggestions
    # instead.
    already_found = {e["test_name"].lower() for e in entries}
    name_only = find_known_test_names(raw_text, _load_alias_index())
    category_index = _load_category_index()
    suggested_test_names = [
        {"test_name": row["test_name"], "category": category_index.get(row["test_name"], "Other")}
        for row in name_only
        if row["test_name"].lower() not in already_found
    ]

    return {
        "filename": file.filename,
        "extracted_tests": entries,
        "suggested_test_names": suggested_test_names,
        "raw_text": raw_text,  # useful for debugging misparsed reports
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Component 3+4+6 combined endpoint. Explanation generation (Component 5,
    the LLM step) is NOT wired in yet — that is Day 4. This endpoint proves
    the validation + retrieval pipeline works end to end through the API.
    """
    test_results = [get_test_info(t.test_name, t.value, t.normal_range, t.category) for t in request.tests]
    medicine_results = [lookup_medicine(m) for m in request.medicines]

    return {
        "tests": test_results,
        "medicines": medicine_results,
    }


@app.get("/test/{test_name}")
def check_test(test_name: str):
    """Single-test lookup, useful for quick manual testing via /docs."""
    return get_test_info(test_name)


@app.get("/medicine/{medicine_name}")
def check_medicine(medicine_name: str):
    """Single-medicine lookup, useful for quick manual testing via /docs."""
    return lookup_medicine(medicine_name)