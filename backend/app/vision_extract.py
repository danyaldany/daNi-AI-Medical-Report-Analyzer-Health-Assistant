"""
Vision-based extraction using Gemini's multimodal (image understanding)
capability. Unlike text-only OCR (Alibaba OCR, Tesseract), a vision model
can directly interpret the image -- including handwritten values and
multi-column table layouts -- because it reasons about the whole image,
not just line-by-line text.

Reuses the same GEMINI_API_KEY already configured for LLM explanation
enhancement (llm_generation.py) -- no new credentials needed.

SAFETY: the model is explicitly instructed to leave a value blank rather
than guess an illegible handwritten number. This is enforced by prompt
instruction, not a hard technical guarantee -- spot-check real results
against real reports before relying on this for a demo.
"""

import os
import base64
import json

from app.llm_generation import GEMINI_API_KEY, ENABLED as LLM_ENABLED, PROVIDER

VISION_ENABLED = bool(GEMINI_API_KEY)

EXTRACTION_PROMPT = """You are extracting lab test results from a photo of a medical report.

CRITICAL INSTRUCTION: Extract EACH AND EVERY printed test row/name on the report, even if the result value is blank or handwritten.
If a row has a blank value, set "value" to null.

For each test row, extract:
- test_name: the printed test name exactly as shown
- value: the result value (read handwriting carefully). If blank/illegible, use null.
- unit: the unit if shown (e.g. mg/dl, g/dl, U/L). If not shown, use null.
- normal_range: the printed reference/normal range for that test, exactly as shown (e.g. "13.5-17.5" or "M: 14-18, F: 11.5-16.5"). If no range is printed, use null.
- category: the panel/section heading this test belongs to (e.g., "Hematology", "Biochemistry", "Serology"). Look at the report's section headings (like "COMPLETE BLOOD COUNT", "LIVER FUNCTION TESTS", etc.). If no section heading exists, infer the category from the test name. If truly unknown, use "Other".

CRITICAL RULES:
- If a printed test name exists but the value field is blank, DO include that row with "value": null.
- Do NOT invent, calculate, or infer any value or range that is not visibly written/printed on the report.
- Only extract what is actually visible in the image.

Return ONLY a valid JSON array, nothing else. Example format:
[{"test_name": "Hemoglobin", "value": "10.6", "unit": "g/dl", "normal_range": "M: 14-18, F: 11.5-16.5", "category": "Hematology"}]

If no tests are found at all, return an empty array: []"""


def extract_tests_with_vision(file_bytes: bytes, mime_type: str = "image/jpeg"):
    """
    Returns a list of {"test_name", "value", "unit", "normal_range", "category"} dicts,
    or None if vision extraction is unavailable/fails (caller should fall back to
    text-only OCR + parsing in that case).
    """
    if not VISION_ENABLED:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=25.0,
        )

        b64_image = base64.b64encode(file_bytes).decode("utf-8")

        response = client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "gemini-3.5-flash-lite"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                        },
                    ],
                }
            ],
            timeout=25.0,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()

        parsed = json.loads(content)
        if not isinstance(parsed, list):
            return None

        # Basic sanity filtering -- never trust the response blindly
        cleaned = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            name = str(item.get("test_name", "")).strip()
            # Allow empty value (null) -- this is the key change for ALL tests
            value = item.get("value")
            if value is not None:
                value = str(value).strip()
                if value == "":
                    value = None
            unit = str(item.get("unit", "")).strip()
            if unit == "":
                unit = None
            normal_range = str(item.get("normal_range", "")).strip()
            if normal_range == "":
                normal_range = None
            category = str(item.get("category", "")).strip()
            if category == "":
                category = "Other"

            if name:  # Only require the name to exist
                cleaned.append({
                    "test_name": name,
                    "value": value,
                    "unit": unit,
                    "normal_range": normal_range,
                    "category": category
                })

        return cleaned

    except Exception as e:
        print(f"[vision_extract.py] Vision extraction failed ({e}); will fall back to text OCR.")
        return None