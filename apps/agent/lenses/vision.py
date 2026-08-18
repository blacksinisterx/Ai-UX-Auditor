"""
"Design Eye" lens: one bounded call to a free OpenRouter vision model for
qualitative layout/hierarchy/whitespace/CTA critique. Deliberately text-only
output -- precise bounding-box coordinates from a free/smaller vision model
are unverified, so geometry stays with OCR boxes + the saliency lens instead.

Model choice: "openrouter/free", the auto-router across whatever's
currently free -- switched to this as the primary choice (not just a
fallback) after directly verifying it: the specific pinned free model
(google/gemma-4-31b-it:free) hit a 429 "temporarily rate-limited upstream"
on literally the first real request, on a fresh key, before this had even
shipped. The auto-router routed around that immediately. Pinned free model
IDs are named here only as a documented alternative if the auto-router
itself ever needs bypassing -- check openrouter.ai/models?fmt=free for a
current one.
"""
import base64
import os

from openai import OpenAI

VISION_MODEL = "openrouter/free"
VISION_MODEL_PINNED_ALTERNATIVE = "google/gemma-4-31b-it:free"

CRITIQUE_PROMPT = """You are a senior product designer reviewing a screenshot of a real UI. \
Give a direct, specific critique covering: layout and visual hierarchy, whitespace and density, \
and whether the primary call-to-action is clear and prominent. Be concrete -- name the specific \
elements you're talking about, not generic advice. Keep it to 4-6 sentences."""


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )


def _image_data_url(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def run_design_eye_lens(image_path: str, model: str = VISION_MODEL) -> str:
    client = _client()
    data_url = _image_data_url(image_path)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CRITIQUE_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError(f"Empty response from {model}")
    return content.strip()
