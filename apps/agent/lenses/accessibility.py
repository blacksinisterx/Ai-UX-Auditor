"""
Deterministic "Rule Book" lens: OCR text extraction, WCAG contrast checking,
and target-size checking. No LLM calls -- this is the real, checkable-by-hand
backbone the rest of Aura's report depends on, not an LLM guessing at pixels.

PaddleOCR note: this targets PaddleOCR 3.x's `predict()` API (returns
OCRResult dicts with rec_texts/rec_scores/rec_boxes), which is a different
shape from the older 2.x `.ocr()` API most tutorials still show -- verified
directly against a real screenshot before writing this, not assumed from
docs. Also: PaddleOCR's default oneDNN/mkldnn CPU backend crashes on this
Windows setup with `NotImplementedError: ConvertPirAttribute2RuntimeAttribute
...`, so `enable_mkldnn=False` is required here.
"""
from dataclasses import asdict, dataclass

import cv2
import numpy as np
from paddleocr import PaddleOCR

_ocr: PaddleOCR | None = None


def get_ocr() -> PaddleOCR:
    global _ocr
    if _ocr is None:
        _ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    return _ocr


@dataclass
class TextBox:
    text: str
    confidence: float
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0


def extract_text_boxes(image_path: str) -> list[TextBox]:
    result = get_ocr().predict(image_path)
    if not result:
        return []
    r0 = result[0]
    boxes = []
    for text, score, box in zip(r0["rec_texts"], r0["rec_scores"], r0["rec_boxes"]):
        x0, y0, x1, y1 = (int(v) for v in box)
        boxes.append(TextBox(text=text, confidence=float(score), x0=x0, y0=y0, x1=x1, y1=y1))
    return boxes


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    def channel(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(rgb1: tuple[float, float, float], rgb2: tuple[float, float, float]) -> float:
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def sample_text_and_background_color(
    image: np.ndarray, box: TextBox
) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
    """Estimate glyph color vs. local background color for a text box region.

    Heuristic: within the box's local neighborhood, the minority extreme
    (darkest or lightest ~15% of pixels) is treated as the glyph strokes,
    and the rest as background -- text usually covers less area than its
    background within a tight crop around it.
    """
    pad = 4
    y0, y1 = max(0, box.y0 - pad), min(image.shape[0], box.y1 + pad)
    x0, x1 = max(0, box.x0 - pad), min(image.shape[1], box.x1 + pad)
    region = image[y0:y1, x0:x1]
    if region.size == 0:
        return None, None

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    flat = gray.flatten()
    dark_thresh = np.percentile(flat, 15)
    light_thresh = np.percentile(flat, 85)
    dark_mask = gray <= dark_thresh
    light_mask = gray >= light_thresh
    text_mask = dark_mask if dark_mask.sum() < light_mask.sum() else light_mask
    bg_mask = ~text_mask

    def mean_bgr(mask: np.ndarray) -> tuple[float, float, float] | None:
        pixels = region[mask]
        if len(pixels) == 0:
            return None
        b, g, r = pixels.mean(axis=0)
        return (float(r), float(g), float(b))

    return mean_bgr(text_mask), mean_bgr(bg_mask)


WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0
LARGE_TEXT_PX = 24  # px height proxy for the ~18.66pt-bold/24pt-regular WCAG "large text" threshold
MIN_TARGET_PX = 44  # WCAG 2.5.5/2.5.8 minimum interactive target size


def check_contrast(image: np.ndarray, boxes: list[TextBox]) -> list[dict]:
    issues = []
    for box in boxes:
        text_rgb, bg_rgb = sample_text_and_background_color(image, box)
        if text_rgb is None or bg_rgb is None:
            continue
        ratio = contrast_ratio(text_rgb, bg_rgb)
        threshold = WCAG_AA_LARGE if box.height >= LARGE_TEXT_PX else WCAG_AA_NORMAL
        issues.append(
            {
                "text": box.text,
                "box": asdict(box),
                "contrast_ratio": round(ratio, 2),
                "threshold": threshold,
                "passes_wcag_aa": ratio >= threshold,
                "text_rgb": [round(c, 1) for c in text_rgb],
                "bg_rgb": [round(c, 1) for c in bg_rgb],
            }
        )
    return issues


def check_target_sizes(boxes: list[TextBox]) -> list[dict]:
    """Flags short, button/link-shaped text boxes under the WCAG minimum
    target size. Heuristic only -- there's no real element/button detector
    here (that's a documented limitation), so this is scoped to boxes that
    look like a short label (<=30 chars, no sentence-ending punctuation)
    rather than every OCR'd text run, to avoid flagging paragraph text.
    """
    issues = []
    for box in boxes:
        looks_like_control = len(box.text) <= 30 and not box.text.rstrip().endswith((".", "?", "!"))
        if not looks_like_control:
            continue
        passes = box.height >= MIN_TARGET_PX and box.width >= MIN_TARGET_PX
        issues.append(
            {
                "text": box.text,
                "box": asdict(box),
                "width": box.width,
                "height": box.height,
                "passes_min_target_size": passes,
            }
        )
    return issues


def run_rule_book_lens(image_path: str) -> dict:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    boxes = extract_text_boxes(image_path)
    return {
        "text_boxes": [asdict(b) for b in boxes],
        "contrast_issues": check_contrast(image, boxes),
        "size_issues": check_target_sizes(boxes),
    }
