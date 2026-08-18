#!/usr/bin/env python
"""Runs MSI-Net saliency prediction in its own process, on purpose.

Real crash found on a GitHub Actions Ubuntu runner: importing TensorFlow
(lenses/attention.py) into the same process as paddleocr/paddlepaddle
(lenses/accessibility.py, already imported by pipeline.py) segfaults --
a hard SIGSEGV that bypasses Python's own exception handling entirely,
so pipeline.py's try/except never even sees it. Isolating this into a
subprocess means the crash, if it recurs, is contained and catchable via
the subprocess's exit code instead of taking down the whole audit run
silently. Didn't reproduce as a segfault on Windows during local testing
(there it was a catchable oneDNN exception) -- verify on the real target
platform, not just locally.

Usage: python run_saliency_subprocess.py <image_path> <heatmap_npy_out>
"""
import sys

import numpy as np

from lenses.attention import predict_saliency


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python run_saliency_subprocess.py <image_path> <heatmap_npy_out>", file=sys.stderr)
        sys.exit(1)
    image_path, heatmap_out_path = sys.argv[1], sys.argv[2]
    heatmap = predict_saliency(image_path)
    np.save(heatmap_out_path, heatmap)


if __name__ == "__main__":
    main()
