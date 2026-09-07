"""
Standalone DashScope/Model Studio API key test — isolated from the rest of
the app, to pinpoint exactly why the key is failing.

Run with: python scripts/test_dashscope_key.py
"""

import os
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv(usecwd=True)
print(f"Loading .env from: {dotenv_path!r}")
load_dotenv(dotenv_path=dotenv_path, override=True)

key = os.environ.get("DASHSCOPE_API_KEY")
if not key:
    print("ERROR: DASHSCOPE_API_KEY not found in environment at all.")
    exit(1)

print(f"Key length: {len(key)}")
print(f"Key starts with: {key[:8]!r}")
print(f"Key ends with: {key[-4:]!r}")
print(f"Has leading/trailing whitespace: {key != key.strip()}")
print()

from openai import OpenAI

workspace_id = os.environ.get("MODEL_STUDIO_WORKSPACE_ID", "ws-v3uyr2u7yhrnnee3")
model_name = os.environ.get("MODEL_STUDIO_MODEL", "qwen3.7-plus")
print(f"Using model: {model_name}")
print()

endpoints_to_try = [
    ("Singapore workspace-dedicated (likely correct)", f"https://{workspace_id}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"),
    ("International shared (legacy)", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
]

for label, base_url in endpoints_to_try:
    print(f"--- Trying {label} endpoint ({base_url}) ---")
    try:
        client = OpenAI(api_key=key.strip(), base_url=base_url, timeout=10.0)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        )
        print("SUCCESS:", response.choices[0].message.content)
        print(f"\n>>> Use the {label} endpoint — it works. <<<")
    except Exception as e:
        print("FAILED:", e)
    print()
