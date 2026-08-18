"""
"Design Eye" lens: one bounded call to Gemini for qualitative
layout/hierarchy/whitespace/CTA critique. Deliberately text-only output --
precise bounding-box coordinates from a vision model are unverified, so
geometry stays with OCR boxes + the saliency lens instead.

Model choice: Gemini via Google's OpenAI-compatible endpoint
("gemini-3.6-flash"). Replaced two earlier free-tier attempts after
directly testing both against the real critique prompt on a real
screenshot, not assuming: OpenRouter's "openrouter/free" auto-router
worked but produced shallow, generic critiques (whichever free model it
landed on that call). Groq's only vision-capable model
("qwen/qwen3.6-27b") produces excellent, specific scene understanding but
is a reasoning model -- on the real prompt it burned its whole response on
visible step-by-step "thinking" and never converged to the requested JSON,
which is a structural mismatch (not a one-off flake) with a
respond-with-only-JSON lens. Gemini 3.6 Flash (gemini-2.5-flash is
deprecated, per Google's own 404 error on that model ID) is a
non-reasoning model that reliably follows the JSON-only instruction and
gives specific, quoted, non-generic critiques.

Structured JSON output, not free-text markdown: an earlier version asked
for a single markdown-formatted paragraph (with **bold** section
headers), which read well in isolation but broke once rendered -- the
frontend showed literal asterisks instead of bold text, since it just
displays the string as plain text. Four separate string fields sidestep
that whole class of bug rather than teaching the frontend to parse
markdown.

Retry + graceful fallback, not just structured parsing: a real user hit
"Expecting value: line 1 column 1 (char 0)" -- the auto-router landed on
some free model that didn't return parseable JSON that run, and the
original code let that single malformed response take down the *entire*
audit, discarding the OCR/contrast/saliency work that had already
succeeded. Since which model answers is out of this app's control by
design (that's the whole point of the auto-router), non-compliant output
is an expected occasional failure mode here, not an edge case -- this
lens now retries once, and if both attempts fail to parse, falls back to
a usable (if less structured) result instead of failing the whole audit.
"""
import base64
import json
import os
import re

from openai import OpenAI

VISION_MODEL = "gemini-3.6-flash"

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

REQUIRED_FIELDS = {"hierarchy", "whitespace", "cta", "flaw"}

Critique = dict[str, str]


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.environ["GEMINI_API_KEY"],
    )


def _image_data_url(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


def _try_parse_critique_json(content: str) -> Critique | None:
    """Best-effort JSON extraction: strips code fences if present, and
    falls back to grabbing the first {...} block if the model added any
    preamble/trailing text despite instructions not to."""
    candidates = [content.strip()]

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())

    brace_match = re.search(r"\{.*\}", content, re.DOTALL)
    if brace_match:
        candidates.append(brace_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and REQUIRED_FIELDS.issubset(parsed.keys()):
            return {k: str(parsed[k]) for k in REQUIRED_FIELDS}
    return None


def _call_once(client: OpenAI, model: str, data_url: str) -> str:
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
    return content


def run_design_eye_lens(image_path: str, model: str = VISION_MODEL) -> Critique:
    client = _client()
    data_url = _image_data_url(image_path)

    last_raw: str | None = None
    for _ in range(2):
        try:
            raw = _call_once(client, model, data_url)
        except Exception:
            continue
        last_raw = raw
        parsed = _try_parse_critique_json(raw)
        if parsed is not None:
            return parsed

    # Both attempts either errored or returned non-compliant output. Don't
    # take the whole audit down over one lens's formatting -- surface
    # whatever text we did get (if any) as a single readable note instead.
    fallback_text = (last_raw or "").strip() or "The vision model did not return a usable critique for this screenshot."
    return {"hierarchy": fallback_text, "whitespace": "", "cta": "", "flaw": ""}
