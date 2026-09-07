import traceback
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
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

# 1. Custom HTTP Middleware for Fail-Safe CORS (Ensures headers on ALL responses)
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={"status": "ok"})
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            # Catch internal errors so CORS headers are not lost on 500 crash
            response = JSONResponse(
                status_code=500,
                content={"detail": str(exc), "traceback": traceback.format_exc()}
            )

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
    try:
        file_bytes = await file.read()

        # Try vision extraction first
        vision_results = None
        try:
            vision_results = extract_tests_with_vision(file_bytes, mime_type=file.content_type or "image/jpeg")
        except Exception as v_err:
            print(f"[Vision Extract Error]: {v_err}")

        if vision_results:
            entries = vision_results
            raw_text = f"[Extracted via vision model — {len(entries)} value(s) found]"
        else:
            raw_text = extract_text_from_image(file_bytes, filename=file.filename)
            entries = parse_report_text(raw_text)

        already_found = {e["test_name"].lower() for e in entries if "test_name" in e}
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
    except Exception as e:
        # Return structured JSON error instead of unhandled 500
        raise HTTPException(status_code=500, detail=f"OCR Processing Error: {str(e)}")


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    test_results = [get_test_info(t.test_name, t.value, t.normal_range, t.category) for t in request.tests]
    medicine_results = [lookup_medicine(m) for m in request.medicines]

    return {
        "tests": test_results,
        "medicines": medicine_results,
    }


@app.get("/test/{test_name}")
def check_test(test_name: str):
    return get_test_info(test_name)


@app.get("/medicine/{medicine_name}")
def check_medicine(medicine_name: str):
    return lookup_medicine(medicine_name)