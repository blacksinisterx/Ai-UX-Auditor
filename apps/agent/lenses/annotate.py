"""Draws failing contrast/size issue boxes onto the screenshot for the
Report Card's "Issues" overlay image. Pure OpenCV drawing, no ML.
"""
import cv2
import numpy as np

CONTRAST_FAIL_COLOR_BGR = (60, 60, 239)  # red
SIZE_FAIL_COLOR_BGR = (11, 165, 245)  # amber


def draw_issue_overlay(image_path: str, contrast_issues: list[dict], size_issues: list[dict]) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    for issue in contrast_issues:
        if issue["passes_wcag_aa"]:
            continue
        box = issue["box"]
        cv2.rectangle(image, (box["x0"], box["y0"]), (box["x1"], box["y1"]), CONTRAST_FAIL_COLOR_BGR, 2)

    for issue in size_issues:
        if issue["passes_min_target_size"]:
            continue
        box = issue["box"]
        cv2.rectangle(image, (box["x0"], box["y0"]), (box["x1"], box["y1"]), SIZE_FAIL_COLOR_BGR, 2)

    return image
