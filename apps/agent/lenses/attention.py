"""
Real local "Psychologist" lens: MSI-Net saliency prediction, run on CPU.
No free API exists for pixel-level saliency heatmaps -- this is genuine
computer vision, not an LLM guessing where a user might look.

Verified directly against a real screenshot before this was written: the
README's documented `tf.keras.models.load_model(hf_dir)` load path fails
under Keras 3 ("legacy SavedModel format is not supported by load_model()"
in this installed tensorflow==2.21/keras==3.15) -- this uses
`tf.saved_model.load(...).signatures["serving_default"]` instead, which
does work, with the real output key `layer_from_saved_model` (not the
README's `"output"`, which is a Keras-model-wrapper-only key name).
CPU inference took ~3.3s for a 1280x800 image on this machine.

IMPORTANT: this module (and only this module) imports TensorFlow. It must
never be imported into the same process as paddleocr/paddlepaddle
(lenses/accessibility.py) -- doing so segfaults on Linux (verified for
real on a GitHub Actions runner: a hard SIGSEGV, not a catchable Python
exception, from the two frameworks' native libraries colliding). That's
exactly why predict_saliency() is invoked from run_saliency_subprocess.py
as a separate process rather than imported directly by pipeline.py; the
cv2/numpy-only helpers that don't need TensorFlow live in
attention_utils.py instead, safe to import anywhere.
"""
import os

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

import numpy as np
import tensorflow as tf
from huggingface_hub import snapshot_download

MODEL_REPO = "alexanderkroner/MSI-Net"

_model = None


def _get_signature():
    global _model
    if _model is None:
        hf_dir = snapshot_download(repo_id=MODEL_REPO)
        loaded = tf.saved_model.load(hf_dir)
        _model = loaded.signatures["serving_default"]
    return _model


def _get_target_shape(original_shape: tuple[int, int]) -> tuple[int, int]:
    aspect_ratio = original_shape[0] / original_shape[1]
    square_mode = abs(aspect_ratio - 1.0)
    landscape_mode = abs(aspect_ratio - 240 / 320)
    portrait_mode = abs(aspect_ratio - 320 / 240)
    best = min(square_mode, landscape_mode, portrait_mode)
    if best == square_mode:
        return (320, 320)
    if best == landscape_mode:
        return (240, 320)
    return (320, 240)


def _preprocess(input_image: np.ndarray, target_shape: tuple[int, int]):
    input_tensor = tf.expand_dims(input_image, axis=0)
    input_tensor = tf.image.resize(input_tensor, target_shape, preserve_aspect_ratio=True)
    vertical_padding = target_shape[0] - input_tensor.shape[1]
    horizontal_padding = target_shape[1] - input_tensor.shape[2]
    vp1, vp2 = vertical_padding // 2, vertical_padding - vertical_padding // 2
    hp1, hp2 = horizontal_padding // 2, horizontal_padding - horizontal_padding // 2
    input_tensor = tf.pad(input_tensor, [[0, 0], [vp1, vp2], [hp1, hp2], [0, 0]])
    return input_tensor, [vp1, vp2], [hp1, hp2]


def _postprocess(output_tensor, vertical_padding, horizontal_padding, original_shape):
    output_tensor = output_tensor[
        :,
        vertical_padding[0] : output_tensor.shape[1] - vertical_padding[1],
        horizontal_padding[0] : output_tensor.shape[2] - horizontal_padding[1],
        :,
    ]
    output_tensor = tf.image.resize(output_tensor, original_shape)
    return output_tensor.numpy().squeeze()


def predict_saliency(image_path: str) -> np.ndarray:
    """Returns a float32 heatmap, same H x W as the input image, values in [0, 1]."""
    sig = _get_signature()
    input_image = tf.keras.utils.load_img(image_path)
    input_image = np.array(input_image, dtype=np.float32)
    original_shape = input_image.shape[:2]
    target_shape = _get_target_shape(original_shape)

    input_tensor, vp, hp = _preprocess(input_image, target_shape)
    output = sig(input_1=input_tensor)["layer_from_saved_model"]
    return _postprocess(output, vp, hp, original_shape)


def run_psychologist_lens(image_path: str) -> dict:
    heatmap = predict_saliency(image_path)
    peak_y, peak_x = np.unravel_index(np.argmax(heatmap), heatmap.shape)
    return {
        "heatmap": heatmap,  # caller persists this as an image; not JSON-serialized here
        "peak_x": int(peak_x),
        "peak_y": int(peak_y),
    }
