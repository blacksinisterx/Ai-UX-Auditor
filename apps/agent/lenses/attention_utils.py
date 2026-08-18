"""Pure numpy/OpenCV helpers for the saliency heatmap -- deliberately kept
separate from attention.py (which imports TensorFlow) so the main pipeline
process can use these without ever loading TensorFlow into a process that
also has paddlepaddle loaded. See run_saliency_subprocess.py for why.
"""
import cv2
import numpy as np


def heatmap_overlay(image_path: str, heatmap: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    norm = ((heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8) * 255).astype(np.uint8)
    color_heat = cv2.applyColorMap(norm, cv2.COLORMAP_INFERNO)
    original = cv2.imread(image_path)
    return cv2.addWeighted(original, 1 - alpha, color_heat, alpha, 0)


def box_attention_overlap(heatmap: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> float:
    """What fraction of the heatmap's total 'weight' falls inside this box."""
    total = heatmap.sum()
    if total <= 0:
        return 0.0
    region = heatmap[max(0, y0) : y1, max(0, x0) : x1]
    return float(region.sum() / total)


def compute_attention_insight(heatmap: np.ndarray, cta: dict) -> dict:
    """The real, checkable headline claim this whole lens exists to produce:
    does visual attention land on the CTA more or less than its size alone
    would predict? A raw overlap percentage (e.g. "gets 3% of attention") is
    only meaningful relative to a baseline -- a small button "deserves" only
    a small share even if it's working perfectly. Comparing overlap share to
    area share turns it into a real over/under-index ratio: >1 means the
    element draws disproportionate attention (it's working), <1 means it's
    getting ignored relative to how much screen space it occupies.
    """
    box = cta["box"]
    x0, y0, x1, y1 = box["x0"], box["y0"], box["x1"], box["y1"]
    img_h, img_w = heatmap.shape[:2]

    overlap = box_attention_overlap(heatmap, x0, y0, x1, y1)
    area_fraction = ((x1 - x0) * (y1 - y0)) / (img_w * img_h)
    density_ratio = overlap / area_fraction if area_fraction > 0 else 0.0

    if density_ratio >= 1.5:
        verdict = "draws disproportionate attention for its size -- it's working"
    elif density_ratio >= 0.7:
        verdict = "gets roughly the attention its size would predict -- unremarkable, neither helped nor hurt"
    else:
        verdict = "is getting visually ignored relative to its size -- attention is going elsewhere"

    return {
        "ctaText": cta["text"],
        "overlapPercent": round(overlap * 100, 2),
        "areaPercent": round(area_fraction * 100, 2),
        "densityRatio": round(density_ratio, 2),
        "verdict": verdict,
    }
