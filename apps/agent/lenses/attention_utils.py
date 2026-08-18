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
