from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from app.knowledge import get_test_info
from app.medicine import lookup_medicine
from app.ocr import extract_text_from_image
from app.report_parser import parse_report_text, find_known_test_names
from app.knowledge import _load_alias_index, _load_category_index
from app.vision_extract import extract_tests_with_vision

app = FastAPI(title="AI Medical Report Analyzer API")

# Custom CORS handling to guarantee headers are NEVER stripped on file uploads
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={"status": "ok"})
    else:
        response = await call_next(request)
        
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

class TestResult(BaseModel):
    test_name: str
    value: Optional[str] = None
    normal_range: Optional[str] = None
    category: Optional[str] = None

class AnalyzeRequest(BaseModel):
    tests: List[TestResult] = []
    medicines: List[str] = []

@app.get("/")
def read_root():
    return {"status": "online", "message": "AI Medical Report Analyzer API is running!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ocr/extract")
async def ocr_extract(file: UploadFile = File(...)):
    file_bytes = await file.read()

    vision_results = extract_tests_with_vision(file_bytes, mime_type=file.content_type or "image/jpeg")

    if vision_results:
        entries = vision_results
        raw_text = f"[Extracted via vision model — {len(entries)} value(s) found]"
    else:
        raw_text = extract_text_from_image(file_bytes, filename=file.filename)
        entries = parse_report_text(raw_text)

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
        "raw_text": raw_text,
    }

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    test_results = [get_test_info(t.test_name, t.value, t.normal_range, t.category) for t in request.tests]
    medicine_results = [lookup_medicine(m) for m in request.medicines]

    return {
        "tests": test_results,
        "medicines": medicine_results,
    }