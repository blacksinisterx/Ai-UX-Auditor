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


def find_cta_candidate(size_issues: list[dict]) -> dict | None:
    """Heuristic CTA guess: the largest short-label box among target-size
    candidates (buttons/links tend to be the biggest short-text elements).
    Used only for the informational attention-overlap insight, never the score.
    """
    if not size_issues:
        return None
    return max(size_issues, key=lambda i: i["width"] * i["height"])
