"""Deterministic "Copy Editor" readability scoring -- pure textstat, no LLM.
The LLM only gets involved later, to rewrite whatever this flags as unclear.
"""
import textstat

LOW_READABILITY_FLESCH_THRESHOLD = 50  # below this, textstat calls it "fairly difficult" or worse


def score_text_block(text: str) -> dict:
    return {
        "text": text,
        "flesch_reading_ease": round(textstat.flesch_reading_ease(text), 1),
        "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(text), 1),
        "flagged_low_readability": textstat.flesch_reading_ease(text) < LOW_READABILITY_FLESCH_THRESHOLD,
    }


def score_text_blocks(texts: list[str]) -> list[dict]:
    # Skip very short strings (button labels, nav items) -- textstat's formulas
    # are unreliable/meaningless below a handful of words, and short labels
    # aren't the "copy" this lens is meant to critique anyway.
    return [score_text_block(t) for t in texts if len(t.split()) >= 6]
