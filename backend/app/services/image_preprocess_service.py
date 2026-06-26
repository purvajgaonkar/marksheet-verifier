"""
image_preprocess_service.py
===========================

Image clean-up BEFORE OCR, using OpenCV.

Tesseract reads text far more accurately from a clean, high-contrast,
black-on-white image than from a raw colour photo. So we run the image
through a small pipeline:

    1. Load the image.
    2. Convert to grayscale (colour does not help text recognition).
    3. Upscale small images (tiny text -> bad OCR).
    4. Denoise (remove camera/scanner grain) when the image looks noisy.
    5. Adaptive threshold (turn it into clean black & white).

Every intermediate image is saved into `forensic_outputs/` so a developer can
open them and SEE exactly what the OCR engine was given. This makes debugging
("why did OCR fail?") much easier for beginners.

Note: these saved intermediates are for *debugging the OCR step*. The deeper
pixel-forensics images (ELA, heatmaps) come later in Phase 4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np


# Minimum width (in pixels) we want before running OCR. Smaller images get
# scaled up so the characters are big enough for Tesseract.
_MIN_WIDTH_FOR_OCR = 1000


def load_image(image_path: str | Path) -> np.ndarray:
    """
    Load an image from disk as an OpenCV array (BGR colour).

    Raises FileNotFoundError if the file is missing or unreadable.
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # cv2.imread can struggle with non-ASCII Windows paths, so we read the raw
    # bytes ourselves and decode them. This is the most Windows-safe approach.
    data = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not decode image (is it a valid image?): {image_path}")
    return image


def _save(image: np.ndarray, output_dir: Path, base_name: str, step: str) -> Path:
    """Save an intermediate image as PNG and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{base_name}__{step}.png"
    # Use imencode + tofile so non-ASCII paths still work on Windows.
    ok, buffer = cv2.imencode(".png", image)
    if ok:
        buffer.tofile(str(out_path))
    return out_path


def _looks_noisy(gray: np.ndarray) -> bool:
    """
    Rough heuristic: estimate noise using the standard deviation of the
    Laplacian. Very high values suggest lots of grain/edges. This is only a
    hint used to decide whether denoising is worthwhile.
    """
    laplacian_std = float(cv2.Laplacian(gray, cv2.CV_64F).std())
    return laplacian_std > 50.0


def preprocess_for_ocr(
    image_path: str | Path,
    output_dir: str | Path,
    base_name: str,
) -> dict:
    """
    Run the full preprocessing pipeline and save intermediate images.

    Parameters
    ----------
    image_path : the image to process (already a PNG/JPG; if the source was a
                 PDF it must already have been rendered to an image).
    output_dir : folder for the debug images (e.g. forensic_outputs/).
    base_name  : a short name used to prefix the saved files (usually the
                 original file's stem).

    Returns
    -------
    dict with:
        "preprocessed_image" : the final black & white numpy array (for OCR)
        "grayscale_image"    : the grayscale numpy array
        "steps"              : { step_name: saved_png_path_as_str }
        "width", "height"    : final image size
        "denoised"           : whether denoising was applied
    """
    output_dir = Path(output_dir)
    steps: dict[str, str] = {}

    # --- 1. Load ---------------------------------------------------------
    original = load_image(image_path)
    steps["01_original"] = str(_save(original, output_dir, base_name, "01_original"))

    # --- 2. Grayscale ----------------------------------------------------
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    steps["02_grayscale"] = str(_save(gray, output_dir, base_name, "02_grayscale"))

    # --- 3. Resize (upscale small images) --------------------------------
    height, width = gray.shape[:2]
    if width < _MIN_WIDTH_FOR_OCR:
        scale = _MIN_WIDTH_FOR_OCR / float(width)
        new_size = (int(width * scale), int(height * scale))
        # INTER_CUBIC gives smoother upscaling, which helps OCR.
        gray = cv2.resize(gray, new_size, interpolation=cv2.INTER_CUBIC)
        steps["03_resized"] = str(_save(gray, output_dir, base_name, "03_resized"))

    # --- 4. Denoise (only if the image looks noisy) ----------------------
    denoised_applied = False
    if _looks_noisy(gray):
        # fastNlMeansDenoising is good at removing grain while keeping edges.
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        denoised_applied = True
        steps["04_denoised"] = str(_save(gray, output_dir, base_name, "04_denoised"))

    # --- 5. Adaptive threshold (clean black & white) ---------------------
    # Adaptive (rather than a single global threshold) handles uneven lighting
    # and shadows common in phone photos of marksheets.
    thresh = cv2.adaptiveThreshold(
        gray,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=31,   # size of the neighbourhood used to pick a threshold
        C=15,           # constant subtracted from the mean; tune for contrast
    )
    steps["05_threshold"] = str(_save(thresh, output_dir, base_name, "05_threshold"))

    final_h, final_w = thresh.shape[:2]
    return {
        "preprocessed_image": thresh,
        "grayscale_image": gray,
        "steps": steps,
        "width": int(final_w),
        "height": int(final_h),
        "denoised": denoised_applied,
    }
