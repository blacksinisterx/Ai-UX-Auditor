"""
Deterministic overall UX score -- three real, checkable-by-hand components,
weighted. No LLM opinion folded in numerically; the AI lenses' output goes
into the report as narrative text instead (layoutCritique, copySuggestions),
never into this number, so the score itself is always defensible from the
raw contrast/size/readability data alone.

Attention-vs-CTA overlap (the saliency lens's headline signal) is
deliberately kept OUT of this formula rather than folded in with a shaky
weighting -- with no real element/button detector, "the CTA" is only a
heuristic guess (the largest short-label OCR box), so it's reported as a
separate, explicit yes/no insight instead of silently distorting the score.
"""
import re


def pass_rate(issues: list[dict], key: str) -> float:
    if not issues:
        return 1.0  # nothing to fail is not a failure
    passing = sum(1 for i in issues if i[key])
    return passing / len(issues)


def readability_score(readability_results: list[dict]) -> float:
    if not readability_results:
        return 100.0
    scores = [max(0.0, min(100.0, r["flesch_reading_ease"])) for r in readability_results]
    return sum(scores) / len(scores)


def compute_overall_score(
    contrast_issues: list[dict],
    size_issues: list[dict],
    readability_results: list[dict],
) -> int:
    contrast_pct = pass_rate(contrast_issues, "passes_wcag_aa") * 100
    size_pct = pass_rate(size_issues, "passes_min_target_size") * 100
    read_pct = readability_score(readability_results)
    weighted = 0.4 * contrast_pct + 0.3 * size_pct + 0.3 * read_pct
    return round(max(0, min(100, weighted)))


# Common CTA verb patterns. A real button/link is disproportionately likely
# to contain one of these; a headline or stat almost never does. This is a
# cheap, deterministic, explainable signal -- no AI call needed -- that
# meaningfully improves on "just pick the biggest short box", which was
# verified to misfire on real data (it picked a page's H1 headline on one
# real test, since large headlines also happen to be short, label-length
# text).
_CTA_PATTERN = re.compile(
    r"\b(sign up|log in|sign in|get started|start free|try (it )?free|buy now|"
    r"subscribe|download|book (a )?demo|request demo|contact (us|sales)|join|"
    r"get (api key|access|the app)|learn more|shop now|add to cart|checkout|"
    r"apply now|register|upgrade|continue)\b",
    re.IGNORECASE,
)

# Real buttons/links are rarely taller than this; excludes headline-sized
# short text (e.g. a two-word H1) from being mistaken for a control.
MAX_CTA_HEIGHT_PX = 70


def find_cta_candidate(size_issues: list[dict]) -> dict | None:
    """Heuristic CTA guess, used only for the informational attention-overlap
    insight, never the score: prefer a button-height box whose text matches a
    common CTA verb; fall back to the largest button-height box if nothing
    matches; fall back further to the largest overall if every candidate is
    headline-sized (better than reporting nothing).
    """
    if not size_issues:
        return None

    button_sized = [i for i in size_issues if i["height"] <= MAX_CTA_HEIGHT_PX]
    keyword_matches = [i for i in button_sized if _CTA_PATTERN.search(i["text"])]

    pool = keyword_matches or button_sized or size_issues
    return max(pool, key=lambda i: i["width"] * i["height"])
