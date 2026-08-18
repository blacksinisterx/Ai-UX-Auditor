"""
Deterministic "what the fix would look like" render: recolors the exact
glyph pixels of each failing-contrast text box to the already-computed
passing color (accessibility.suggest_fixed_text_color), instead of asking
a generative model to imagine a fix. No AI call, no hallucination risk --
every recolored pixel traces back to a real WCAG contrast computation,
same "proof, not vibes" principle as the rest of the Rule Book lens.

Target-size issues aren't visually re-rendered here: padding a real
button without redrawing the surrounding layout would look fake. Those
stay as text suggestions in the Rule Book tab.

Free-tier note: tested Gemini's image-generation models directly (not
assumed) as a generative alternative -- all three (gemini-2.5-flash-image,
gemini-3-pro-image, gemini-3.1-flash-image) return a hard 429 with
`limit: 0` on the free tier, i.e. image generation isn't available at all
without enabling billing. This pixel-recolor approach is free and, being
deterministic, more honest to the project's own "checkable, not a guess"
premise anyway.
"""
import cv2
import numpy as np

from lenses.accessibility import text_pixel_mask

RECOLOR_PAD = 4


def render_fixed_screenshot(image_path: str, contrast_issues: list[dict]) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    for issue in contrast_issues:
        if issue["passes_wcag_aa"] or issue["fixed_rgb"] is None:
            continue
        box = issue["box"]
        y0, y1 = max(0, box["y0"] - RECOLOR_PAD), min(image.shape[0], box["y1"] + RECOLOR_PAD)
        x0, x1 = max(0, box["x0"] - RECOLOR_PAD), min(image.shape[1], box["x1"] + RECOLOR_PAD)
        region = image[y0:y1, x0:x1]
        if region.size == 0:
            continue
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        mask = text_pixel_mask(gray)
        r, g, b = issue["fixed_rgb"]
        region[mask] = [b, g, r]

    return image
