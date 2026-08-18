"""
"Copy Editor" lens: one bounded Groq call rewriting every flagged
low-readability text block from readability.py at once -- never one call
per snippet, per the plan's bounded-calls rule.
"""
import json
import os

from openai import OpenAI

TEXT_MODEL = "openai/gpt-oss-120b"

PROMPT_TEMPLATE = """You are a copy editor improving UI text for clarity. For each numbered snippet below, \
write a clearer, shorter rewrite that keeps the same meaning. Respond with ONLY a JSON array of strings, \
one rewrite per snippet, in the same order. No explanation, no markdown fences.

Snippets:
{snippets}"""


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
    )


def run_copy_editor_lens(flagged_texts: list[str]) -> list[dict]:
    """Returns [{"original": str, "suggestion": str}, ...] for each flagged text."""
    if not flagged_texts:
        return []

    snippets = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(flagged_texts))
    response = _client().chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(snippets=snippets)}],
        temperature=0.3,
    )
    content = (response.choices[0].message.content or "").strip()
    # Models occasionally wrap JSON in markdown fences despite instructions; strip if present.
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    rewrites = json.loads(content)
    if len(rewrites) != len(flagged_texts):
        raise ValueError(f"Expected {len(flagged_texts)} rewrites, got {len(rewrites)}")
    return [{"original": orig, "suggestion": rw} for orig, rw in zip(flagged_texts, rewrites)]
