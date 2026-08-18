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

# Below this, a "text" reading is more likely PaddleOCR hallucinating a
# character onto a logo/icon than real text. Verified against a real
# screenshot (openrouter.ai) before picking this number: genuine UI text
# clustered at confidence >=0.95 (median ~0.995), while logo misreads --
# the ChatGPT icon read as "安", Qwen's as "⑤" -- scored 0.14-0.87. This
# threshold sits in the real gap between those two clusters, not a guess.
MIN_OCR_CONFIDENCE = 0.90

# Single-character reads pass the confidence filter above just fine when
# the glyph genuinely looks like a real letter -- which is exactly what
# happens with logo marks that are themselves letterforms (Mistral's "M",
# Zhipu's "Z", a stylized "A"). High confidence, still not real text: a
# single character is essentially never meaningful copy a user reads, so
# it's excluded from every check (contrast, target-size) rather than
# trying to separately special-case "logo-shaped" boxes.
MIN_TEXT_CHARS = 2

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
        if score < MIN_OCR_CONFIDENCE or len(text.strip()) < MIN_TEXT_CHARS:
            continue
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


def text_pixel_mask(gray: np.ndarray) -> np.ndarray:
    """Otsu-thresholds the region into two classes, then treats the
    minority class as glyph strokes and the majority as background --
    text usually covers less area than its background within a tight
    crop around it. Shared by contrast sampling (read colors) and the
    fixed-screenshot renderer (write colors).

    A fixed 15th/85th-percentile split was tried first but silently broke
    on the most extreme real cases: verified directly against a 1.11:1
    "Log in" label where text and background are both near-black, where a
    fixed percentile just re-splits noise instead of finding the actual
    glyph shape. Otsu adaptively finds the threshold that best separates
    the region's true bimodal distribution, which correctly recovered
    that case (and held up on a moderate 3.82:1 case too) rather than
    assuming a fixed split point works everywhere.
    """
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = mask > 0
    return ~mask if mask.sum() > mask.size / 2 else mask


def sample_text_and_background_color(
    image: np.ndarray, box: TextBox
) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
    """Estimate glyph color vs. local background color for a text box region."""
    pad = 4
    y0, y1 = max(0, box.y0 - pad), min(image.shape[0], box.y1 + pad)
    x0, x1 = max(0, box.x0 - pad), min(image.shape[1], box.x1 + pad)
    region = image[y0:y1, x0:x1]
    if region.size == 0:
        return None, None

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    text_mask = text_pixel_mask(gray)
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


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def suggest_fixed_text_color(
    text_rgb: tuple[float, float, float], bg_rgb: tuple[float, float, float], threshold: float
) -> tuple[float, float, float]:
    """Binary-searches a blend of the existing text color toward whichever
    pure extreme (black or white) actually reaches a higher contrast
    ratio against this background, until it clears the threshold. A
    concrete, checkable suggestion -- not "make it darker," an actual
    color that passes.

    Real bug found by testing the most extreme case directly (a "Log in"
    label at a 1.11:1 ratio, text and background both near-black): picking
    the target by "whichever direction locally increases contrast from
    the current color" -- i.e. comparing bg_lum vs text_lum -- breaks when
    both colors sit in the same narrow dark (or light) cluster. Darkening
    text that's already near-black toward pure black only reaches ~1.16:1
    against a near-black background -- it can never reach 4.5:1, no matter
    how far the blend goes, because the saturating extreme itself isn't
    far enough from the background. Comparing the two extremes' actual
    achievable ratios (not just local direction) picks white here instead,
    correctly reaching the real fix.
    """
    black_contrast = contrast_ratio((0.0, 0.0, 0.0), bg_rgb)
    white_contrast = contrast_ratio((255.0, 255.0, 255.0), bg_rgb)
    target = (0.0, 0.0, 0.0) if black_contrast >= white_contrast else (255.0, 255.0, 255.0)

    lo, hi = 0.0, 1.0
    best = text_rgb
    for _ in range(20):
        mid = (lo + hi) / 2
        candidate = tuple(text_rgb[i] + (target[i] - text_rgb[i]) * mid for i in range(3))
        if contrast_ratio(candidate, bg_rgb) >= threshold:
            best = candidate
            hi = mid
        else:
            lo = mid
    return best


def check_contrast(image: np.ndarray, boxes: list[TextBox]) -> list[dict]:
    issues = []
    for box in boxes:
        text_rgb, bg_rgb = sample_text_and_background_color(image, box)
        if text_rgb is None or bg_rgb is None:
            continue
        ratio = contrast_ratio(text_rgb, bg_rgb)
        threshold = WCAG_AA_LARGE if box.height >= LARGE_TEXT_PX else WCAG_AA_NORMAL
        passes = ratio >= threshold
        suggestion = None
        fixed_rgb = None
        if not passes:
            fixed_rgb = suggest_fixed_text_color(text_rgb, bg_rgb, threshold)
            fixed_hex = _rgb_to_hex(fixed_rgb)
            suggestion = (
                f"Contrast is {ratio:.2f}:1, needs {threshold}:1. Shift the text color to about "
                f"{fixed_hex} (or lighten/darken the background instead) to clear it."
            )
        issues.append(
            {
                "text": box.text,
                "box": asdict(box),
                "contrast_ratio": round(ratio, 2),
                "threshold": threshold,
                "passes_wcag_aa": passes,
                "text_rgb": [round(c, 1) for c in text_rgb],
                "bg_rgb": [round(c, 1) for c in bg_rgb],
                "suggestion": suggestion,
                "fixed_rgb": [round(c, 1) for c in fixed_rgb] if fixed_rgb else None,
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
        suggestion = None
        if not passes:
            suggestion = (
                f"Currently {box.width}x{box.height}px, needs at least {MIN_TARGET_PX}x{MIN_TARGET_PX}px. "
                f"Add padding around this element so the full tappable/clickable area clears the minimum -- "
                f"the visible text can stay the same size."
            )
        issues.append(
            {
                "text": box.text,
                "box": asdict(box),
                "width": box.width,
                "height": box.height,
                "passes_min_target_size": passes,
                "suggestion": suggestion,
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
