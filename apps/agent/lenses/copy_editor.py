"""
"Copy Editor" lens: one bounded Groq call that does two things at once --
rewrites every flagged low-readability text block, AND synthesizes an
executive summary from the OTHER three lenses' findings (score breakdown,
the Design Eye's flaw, the real attention-vs-CTA number). Still exactly
one call, per the plan's bounded-calls rule; it just does more with it,
so the report has one real "so what" headline instead of four disconnected
tabs the reader has to synthesize themselves.
"""
import json
import os
import re

from openai import OpenAI

TEXT_MODEL = "openai/gpt-oss-120b"

PROMPT_TEMPLATE = """You are auditing a real website's UX. You're given the raw findings from three other \
independent checks (real WCAG contrast/size math, a saliency model's attention data, and a layout critique) \
plus a list of low-readability copy snippets. Do two things:

1. Write a 2-3 sentence executive summary of the single most important, specific, concrete takeaway from \
these findings combined -- not a recap of every number, the ONE thing that matters most. Reference actual \
numbers and quoted elements from the findings below. No generic filler.
2. For each numbered copy snippet, write a clearer, shorter rewrite that keeps the same meaning. If there are \
no snippets, return an empty array for copyRewrites.

FINDINGS:
{findings}

SNIPPETS TO REWRITE:
{snippets}

Respond with ONLY a JSON object, no markdown fences, no other text:
{{
  "executiveSummary": "...",
  "copyRewrites": ["...", "..."]
}}
The copyRewrites array must have exactly {snippet_count} entries, in the same order as the snippets, or be \
empty if there were no snippets."""

REQUIRED_FIELDS = {"executiveSummary", "copyRewrites"}


def _client() -> OpenAI:
    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
    )


def _try_parse(content: str, snippet_count: int) -> dict | None:
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
        if not isinstance(parsed, dict) or not REQUIRED_FIELDS.issubset(parsed.keys()):
            continue
        rewrites = parsed["copyRewrites"]
        if not isinstance(rewrites, list) or len(rewrites) != snippet_count:
            continue
        return {"executiveSummary": str(parsed["executiveSummary"]), "copyRewrites": [str(r) for r in rewrites]}
    return None


def run_synthesis_lens(
    flagged_texts: list[str],
    score: int,
    contrast_fail_count: int,
    size_fail_count: int,
    attention_insight: dict | None,
    design_flaw: str,
) -> dict:
    """Returns {"executiveSummary": str, "copySuggestions": [{"original","suggestion"}, ...]}."""
    findings_lines = [
        f"- Overall score: {score}/100",
        f"- Contrast: {contrast_fail_count} elements fail WCAG AA",
        f"- Target size: {size_fail_count} elements are under the 44x44px minimum tap target",
        f"- Design critique's flagged flaw: {design_flaw}",
    ]
    if attention_insight:
        findings_lines.append(
            f"- Attention data: the likely primary call-to-action ('{attention_insight['ctaText']}') "
            f"occupies {attention_insight['areaPercent']}% of the screen but receives "
            f"{attention_insight['overlapPercent']}% of total visual attention "
            f"(a {attention_insight['densityRatio']}x density ratio -- 1.0 is exactly proportional to its size) "
            f"-- {attention_insight['verdict']}."
        )
    findings = "\n".join(findings_lines)
    snippets = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(flagged_texts)) or "(none)"

    prompt = PROMPT_TEMPLATE.format(findings=findings, snippets=snippets, snippet_count=len(flagged_texts))

    client = _client()
    last_content = ""
    for _ in range(2):
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = (response.choices[0].message.content or "").strip()
        last_content = content
        parsed = _try_parse(content, len(flagged_texts))
        if parsed is not None:
            return {
                "executiveSummary": parsed["executiveSummary"],
                "copySuggestions": [
                    {"original": orig, "suggestion": rw}
                    for orig, rw in zip(flagged_texts, parsed["copyRewrites"])
                ],
            }

    # Both attempts failed to produce compliant JSON -- don't take the whole
    # audit down over this one call; surface whatever text came back (if
    # any) as the summary and skip copy rewrites rather than crashing.
    fallback_summary = last_content.strip() or "No summary available for this audit."
    return {"executiveSummary": fallback_summary, "copySuggestions": []}
