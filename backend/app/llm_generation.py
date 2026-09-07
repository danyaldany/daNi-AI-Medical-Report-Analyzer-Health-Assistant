"""
Optional LLM-based explanation enhancement. Supports Alibaba Cloud Model
Studio (DashScope) OR Google Gemini (OpenAI-compatible endpoint) -- both
are permitted per the hackathon's re-evaluation email, which explicitly
states participants are "not restricted to a single toolchain" and may use
"your own API keys, connected to the platform of your choice."

CRITICAL design constraint: this NEVER replaces the verified static
explanation from knowledge_base.json as the source of truth. It only tries
to rephrase/personalize it using the value and abnormal status already
computed deterministically elsewhere. If no key is set, the call fails, or
it's slow, this silently falls back to the original static explanation --
the pipeline must never break or hang because of this.

This is also ONLY used for tests already in the verified knowledge base --
never called for unknown tests, and it never has authority to invent new
medical claims. The system prompt explicitly forbids diagnostic language.
"""

import os
from dotenv import load_dotenv

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
MODEL_STUDIO_WORKSPACE_ID = os.environ.get("MODEL_STUDIO_WORKSPACE_ID")

# Provider selection: Gemini first if configured (free tier, no billing
# setup needed -- fastest to get working), otherwise Alibaba Model Studio
# if that's configured, otherwise disabled (static explanations only).
if GEMINI_API_KEY:
    PROVIDER = "gemini"
    API_KEY = GEMINI_API_KEY
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    MODEL_NAME = os.environ.get("LLM_MODEL", "gemini-3.5-flash-lite")
elif DASHSCOPE_API_KEY:
    PROVIDER = "alibaba_model_studio"
    API_KEY = DASHSCOPE_API_KEY
    if MODEL_STUDIO_WORKSPACE_ID:
        BASE_URL = f"https://{MODEL_STUDIO_WORKSPACE_ID}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    else:
        BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    MODEL_NAME = os.environ.get("LLM_MODEL", "qwen3.7-plus")
else:
    PROVIDER = None
    API_KEY = None
    BASE_URL = None
    MODEL_NAME = None

ENABLED = PROVIDER is not None

if ENABLED:
    print(f"[llm_generation.py] Using provider: {PROVIDER}, model: {MODEL_NAME} — LLM enhancement active.")
else:
    print("[llm_generation.py] No GEMINI_API_KEY or DASHSCOPE_API_KEY set — using static explanations only (this is safe and expected if you haven't set this up yet).")

SYSTEM_PROMPT = """You are a medical assistant explaining lab results to a patient in simple, clear language.

You will receive: test_name, patient_value, reference_range, abnormal_status, and a static verified explanation.

**INSTRUCTIONS BASED ON STATUS:**

1. If status is "normal":
    - Rephrase the static explanation naturally and personally.
    - Keep it to 4-5 sentences per language.

2. If status is "abnormal_low":
    - Start with: "Your {test_name} is {value}, which is lower than the normal range ({range})."
    - Add a specific reason using the matching association below: "This may happen due to [specific reason for low value]."
    - Add a brief effect using only context supported by the static explanation: "This can sometimes lead to [symptom/effect]."
    - End with: "Please consult your doctor for a complete evaluation."

3. If status is "abnormal_high":
    - Start with: "Your {test_name} is {value}, which is higher than the normal range ({range})."
    - Add a specific reason using the matching association below: "This may happen due to [specific reason for high value]."
    - Add a brief effect using only context supported by the static explanation: "This can sometimes be associated with [symptom/context]."
    - End with: "Please consult your doctor for a complete evaluation."

**SPECIFIC REASONING RULES (Use these associations based on test_name):**
- Low Hemoglobin/HCT/MCH/MCHC: iron deficiency, blood loss, or nutritional deficiencies.
- High Hemoglobin/HCT: dehydration, smoking, or lung conditions.
- Low MCV: iron deficiency or thalassemia trait.
- High MCV: B12 or folate deficiency.
- Low Platelets: infections or bone marrow suppression.
- High Platelets: inflammation, infection, or iron deficiency (reactive).
- Low Neutrophils: viral infections or bone marrow issues.
- High Neutrophils: bacterial infections or inflammation.
- Low Creatinine: decreased muscle mass.
- High Creatinine: dehydration or kidney function changes.

**SAFETY RULES:**
- NEVER say "you have" or diagnose. Always use "may happen due to", "could be associated with", or "might indicate".
- Do NOT invent rare diseases or add unsupported claims. Use only the common associations listed above and the static explanation for general test facts and effects.
- Use the static explanation for the general description of what the test measures.
- Output MUST be 4-5 sentences per language.
- Output ONLY valid JSON with keys "explanation_en" and "explanation_ur".
"""


def enhance_explanation(test_name: str, value: str, abnormal_status: str, static_explanation_en: str, static_explanation_ur: str, timeout_seconds: float = 20.0, reference_range: str = None):
    """
    Returns (explanation_en, explanation_ur) -- either LLM-enhanced or, on
    ANY failure/timeout/disabled state, the original static text unchanged.
    Never raises.
    """
    if not ENABLED:
        return static_explanation_en, static_explanation_ur

    try:
        from openai import OpenAI

        client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=timeout_seconds)

        user_prompt = f"""Test name: {test_name}
Patient's value: {value if value else "(not provided)"}
    Abnormal status: {abnormal_status if abnormal_status else "(not evaluated)"}
    Reference range: {reference_range if reference_range else "(not provided)"}
    Static explanation (English): {static_explanation_en}
    Static explanation (Urdu): {static_explanation_ur}

    Explain the result in both languages, using the patient's value, reference range, and abnormal status for relevant context. Respond with JSON only."""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            timeout=timeout_seconds,
        )

        import json
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        parsed = json.loads(content)

        new_en = parsed.get("explanation_en", "").strip()
        new_ur = parsed.get("explanation_ur", "").strip()

        if len(new_en) < 50 or len(new_ur) < 50:
            return static_explanation_en, static_explanation_ur

        return new_en, new_ur

    except Exception as e:
        print(f"[llm_generation.py] Enhancement failed ({e}); using static explanation.")
        return static_explanation_en, static_explanation_ur
