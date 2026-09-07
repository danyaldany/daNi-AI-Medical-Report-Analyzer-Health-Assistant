"""
Component 2 (OCR Extraction).

Calls Alibaba Cloud's OCR API to extract raw text from an uploaded report
image. Requires ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET
environment variables.

IMPORTANT: I do not have access to Alibaba Cloud credentials or the ability
to make live calls to their OCR API from this sandbox, so the exact request
shape below has NOT been tested end-to-end against the real service. You
will need to verify the request/response format against Alibaba Cloud's
current OCR API documentation (General Text Recognition) when you wire in
your real credentials, and adjust if their current API differs.

Without credentials set, this module falls back to MOCK mode so Day 3 can
be built and tested end-to-end before real OCR credentials are wired in.
"""

import os
import io
import re
from dotenv import load_dotenv

# Bug fix: load_dotenv(override=True) with NO explicit path uses dotenv's
# own search logic, which was resolving to a DIFFERENT (likely empty) .env
# file somewhere else on disk -- not backend/.env. Forcing an explicit,
# absolute path removes all ambiguity, same pattern as BASE_DIR in
# knowledge.py.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

ACCESS_KEY_ID = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
ACCESS_KEY_SECRET = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")

MOCK_MODE = not (ACCESS_KEY_ID and ACCESS_KEY_SECRET)

if MOCK_MODE:
    print(f"[ocr.py] Looked for .env at: {_ENV_PATH}")
    print("[ocr.py] WARNING: Running in MOCK MODE — no real OCR is happening. "
          "Extracted values are hardcoded sample data, not from the uploaded image.")
else:
    print("[ocr.py] Alibaba Cloud OCR credentials found — real OCR mode active.")

# A sample mock OCR result, standing in for real Alibaba Cloud OCR output,
# so the rest of the pipeline (parsing, manual review, analysis) can be
# built and tested without live API access.
MOCK_OCR_TEXT = """
COMPLETE BLOOD COUNT REPORT
Hemoglobin (Hb)      11.2   g/dL   (13.5-17.5)
White Blood Cell Count  9800   cells/mcL  (4500-11000)
Platelet Count       410000  /mcL   (150000-450000)
Fasting Blood Sugar (FBS)  126   mg/dL  (70-100)
"""


def _tesseract_fallback(file_bytes: bytes) -> str:
    """
    Local OCR fallback using Tesseract (open-source, no API/credentials
    needed). Used automatically when Alibaba Cloud OCR errors out (e.g.
    service not activated, quota exceeded, network issue) -- so a
    credentials/activation problem on one provider doesn't mean the whole
    upload flow stops working. Image files only; PDFs are not converted
    here (falls through to manual entry if this also can't handle it).

    Includes automatic orientation correction: real-world phone photos of
    reports are very often rotated (confirmed while testing against a real
    report photo -- Tesseract's own text output was near-unreadable until
    rotation was corrected using its orientation-detection feature).
    """
    try:
        import io as _io
        from PIL import Image
        import pytesseract

        # Auto-detect Tesseract's executable location. Checked in order:
        # 1. TESSERACT_CMD in .env (most reliable -- set this if the below don't work)
        # 2. Whatever's already on PATH (pytesseract's default behavior)
        # 3. A few common Windows install locations
        env_path = os.environ.get("TESSERACT_CMD")
        if env_path and os.path.exists(env_path):
            pytesseract.pytesseract.tesseract_cmd = env_path
        elif os.name == "nt":
            candidate_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"D:\software\Tesseract-OCR\tesseract.exe",  # confirmed install location
            ]
            for candidate in candidate_paths:
                if os.path.exists(candidate):
                    pytesseract.pytesseract.tesseract_cmd = candidate
                    break

        image = Image.open(_io.BytesIO(file_bytes))

        # Auto-detect and correct rotation. Tesseract's OSD "Rotate: N"
        # means "rotate N degrees clockwise to fix it"; PIL's rotate()
        # is counter-clockwise for positive angles, so we negate N.
        try:
            osd = pytesseract.image_to_osd(image)
            rotate_match = re.search(r"Rotate:\s*(\d+)", osd)
            if rotate_match:
                degrees = int(rotate_match.group(1))
                if degrees != 0:
                    image = image.rotate(-degrees, expand=True)
        except Exception:
            pass  # OSD can fail on some images (e.g. too little text) -- fine, just skip correction

        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"[OCR_ERROR] Alibaba Cloud OCR failed, and the local Tesseract fallback also failed: {e}"


def extract_text_from_image(file_bytes: bytes, filename: str = "") -> str:
    """
    Component 2 entry point. Returns raw extracted text from the report image.

    Order of attempts: Alibaba Cloud OCR (primary, if credentials are set)
    -> Tesseract (automatic local fallback if Alibaba fails) -> mock data
    (only if no credentials were ever configured, for local dev).

    Real integration (verify against current Alibaba Cloud OCR docs):
    Alibaba Cloud's OCR API is typically called via their SDK
    (alibabacloud_ocr_api20210707 or similar) or a signed REST call, passing
    the image as base64 or a URL, and returning recognized text blocks.
    """
    if MOCK_MODE:
        return MOCK_OCR_TEXT

    # --- Real Alibaba Cloud OCR call (NOT tested — verify against current docs) ---
    try:
        from alibabacloud_ocr_api20210707.client import Client as OcrClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_ocr_api20210707 import models as ocr_models
        from alibabacloud_tea_util import models as util_models

        config = open_api_models.Config(
            access_key_id=ACCESS_KEY_ID,
            access_key_secret=ACCESS_KEY_SECRET,
            endpoint="ocr-api.cn-hangzhou.aliyuncs.com",
        )
        client = OcrClient(config)
        request = ocr_models.RecognizeGeneralRequest(body=io.BytesIO(file_bytes))
        runtime = util_models.RuntimeOptions()
        response = client.recognize_general_with_options(request, runtime)
        return response.body.data  # NOTE: verify actual response field name
    except Exception as e:
        print(f"[ocr.py] Alibaba Cloud OCR failed ({e}); trying Tesseract fallback...")
        return _tesseract_fallback(file_bytes)
