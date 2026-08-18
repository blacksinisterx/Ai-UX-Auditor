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
shipped (and again on a later retest -- consistently unavailable, not a
one-off). The auto-router routed around that immediately. Pinned free
model IDs are named here only as a documented alternative if the
auto-router itself ever needs bypassing -- check
openrouter.ai/models?fmt=free for a current one.

Structured JSON output, not free-text markdown: an earlier version asked
for a single markdown-formatted paragraph (with **bold** section
headers), which read well in isolation but broke once rendered -- the
frontend showed literal asterisks instead of bold text, since it just
displays the string as plain text. Four separate string fields sidestep
that whole class of bug rather than teaching the frontend to parse
markdown.
"""
import base64
import json
import os

from openai import OpenAI

VISION_MODEL = "openrouter/free"
VISION_MODEL_PINNED_ALTERNATIVE = "google/gemma-4-31b-it:free"

CRITIQUE_PROMPT = """You are a senior product designer reviewing a screenshot of a real UI. In every field, \
name the actual visible text, button, or element you're referring to -- quote it. Never use generic filler \
like "clean and modern," "intuitive," or "user-friendly" without pointing at the specific thing that makes it so.

Respond with ONLY a JSON object with exactly these four string fields, no markdown fences, no other text:
{
  "hierarchy": "What does the eye land on first, second, third? Name the actual headline/element text. 1-2 sentences.",
  "whitespace": "Is spacing generous or cramped, and where specifically? 1-2 sentences.",
  "cta": "Name the actual button text. Is it the most visually dominant clickable element, or does something else compete with it -- name that competitor if so. 1-2 sentences.",
  "flaw": "One specific, fixable problem -- not a vague suggestion. Point at the exact element and say what's wrong with it. 1-2 sentences."
}"""

Critique = dict[str, str]


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


def _parse_critique_json(content: str) -> Critique:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    parsed = json.loads(text)
    required = {"hierarchy", "whitespace", "cta", "flaw"}
    missing = required - parsed.keys()
    if missing:
        raise ValueError(f"Critique JSON missing fields: {missing}")
    return {k: str(parsed[k]) for k in required}


def run_design_eye_lens(image_path: str, model: str = VISION_MODEL) -> Critique:
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
    return _parse_critique_json(content)
