"""
forensics_service.py
====================

LOCAL pixel/image forensics. Everything here uses only OpenCV, Pillow, NumPy
(and PyMuPDF via pdf_service for PDFs) — no ML models, no GPU, no cloud.

VERY IMPORTANT — read this before trusting any output
-----------------------------------------------------
These signals are WEAK EVIDENCE ONLY. They do NOT prove a document is fake or
forged. Compression, scanning, mobile-camera capture, screenshots, WhatsApp
forwarding, and PDF conversion all create artefacts that look exactly like
"tampering" to these algorithms. Treat every output as a review aid for a human,
never as a verdict.

What this module produces, per case, inside:
    forensic_outputs/<case_id>/
        normalized.png      - a clean RGB/PNG copy of the (first page of the) doc
        ela.png             - Error-Level-Analysis style difference view
        edge_map.png        - Canny edge map
        sharpness_map.png   - local sharpness heatmap
        noise_map.png       - local noise heatmap
        anomaly_heatmap.png - combined weak-signal heatmap

run_forensics() ties them together and returns a JSON-friendly dict. It NEVER
raises: on any failure it returns {"available": false, "error": ...} so the
upload/analysis pipeline keeps working.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageChops

from app.services import pdf_service, risk_service

# Cap the working resolution so forensics stays fast on large scans/photos.
_MAX_DIM = 1600
_JPEG_QUALITY = 85
_EPS = 1e-6

# Shared limitation notes attached to every forensics result.
_LIMITATIONS = [
    "Image forensics are weak evidence only and do not prove tampering.",
    "Scanning, compression, mobile capture, screenshots, and PDF conversion can create false positives.",
    "Official board / DigiLocker verification is stronger than pixel analysis.",
    "A human reviewer must interpret these visualizations.",
]


# ---------------------------------------------------------------------------
# Small Windows-safe image IO helpers (handle non-ASCII paths)
# ---------------------------------------------------------------------------
def _imread_color(path: str | Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    return img


def _imwrite(path: str | Path, image: np.ndarray) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix or ".png"
    ok, buffer = cv2.imencode(ext, image)
    if ok:
        buffer.tofile(str(path))
    return path


def _level_for(score: float) -> str:
    """Bucket a 0..1 score into a conservative low/medium/high level."""
    if score < 0.34:
        return "low"
    if score < 0.67:
        return "medium"
    return "high"


def _resize_max(image: np.ndarray, max_dim: int = _MAX_DIM) -> np.ndarray:
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest > max_dim:
        scale = max_dim / float(longest)
        image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return image


def _block_cv(arr: np.ndarray, blocks: int = 8) -> float:
    """
    Coefficient of variation (std / mean) of an array's value averaged over a
    grid of blocks. A higher value means the quantity (sharpness, noise) varies
    a lot across the page, which *can* hint at a pasted region — but is also
    completely normal for text vs. whitespace, so we keep its influence small.
    """
    h, w = arr.shape[:2]
    bh, bw = max(1, h // blocks), max(1, w // blocks)
    means = []
    for y in range(0, h, bh):
        for x in range(0, w, bw):
            block = arr[y : y + bh, x : x + bw]
            if block.size:
                means.append(float(block.mean()))
    means = np.asarray(means, dtype=np.float32)
    m = float(means.mean())
    if m <= _EPS:
        return 0.0
    return float(means.std() / m)


def _norm01(arr: np.ndarray) -> np.ndarray:
    """Scale a float array to 0..1 for use as a combinable intensity map."""
    arr = arr.astype(np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi - lo <= _EPS:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - lo) / (hi - lo)


# ---------------------------------------------------------------------------
# A. Normalize the input into a clean RGB PNG
# ---------------------------------------------------------------------------
def prepare_image_for_forensics(
    input_file: str | Path, case_id: str, forensic_root: str | Path
) -> tuple[Path, Path]:
    """
    Accept a PDF/JPG/JPEG/PNG, render the first page if it is a PDF, and save a
    normalized RGB PNG at forensic_outputs/<case_id>/normalized.png.

    Returns (output_dir, normalized_png_path).
    """
    forensic_root = Path(forensic_root)
    out_dir = forensic_root / str(case_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_file = Path(input_file)
    if pdf_service.is_pdf(input_file):
        rendered = out_dir / "_source_page1.png"
        pdf_service.render_first_page_to_png(input_file, rendered)
        image = _imread_color(rendered)
    else:
        image = _imread_color(input_file)

    image = _resize_max(image)
    normalized_path = out_dir / "normalized.png"
    _imwrite(normalized_path, image)
    return out_dir, normalized_path


# ---------------------------------------------------------------------------
# B. Error Level Analysis (ELA)
# ---------------------------------------------------------------------------
def generate_ela_image(image_path: str | Path, output_dir: str | Path) -> dict:
    """
    ELA re-saves the image as JPEG and highlights regions that change a lot
    under recompression. Edited/pasted regions sometimes stand out — but ELA is
    unreliable for PNGs, scanned PDFs, and already-recompressed images.
    """
    output_dir = Path(output_dir)
    ela_path = output_dir / "ela.png"

    original = Image.open(image_path).convert("RGB")
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=_JPEG_QUALITY)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    diff = ImageChops.difference(original, recompressed)

    # Visualization: stretch the difference so it is actually visible.
    extrema = diff.getextrema()
    max_channel = max(hi for _, hi in extrema) or 1
    scale = 255.0 / max_channel
    ela_vis = diff.point(lambda v: min(255, int(v * scale)))
    ela_vis.save(ela_path)

    # Numeric score: 95th percentile of the per-pixel mean difference, scaled
    # conservatively. PNG text edges naturally produce JPEG ringing, so we use a
    # high divisor to avoid over-flagging.
    diff_gray = np.asarray(diff, dtype=np.float32).mean(axis=2)
    p95 = float(np.percentile(diff_gray, 95))
    mean_diff = float(diff_gray.mean())
    score = float(np.clip(p95 / 80.0, 0.0, 1.0))

    return {
        "name": "ELA difference",
        "score": round(score, 3),
        "level": _level_for(score),
        "path": str(ela_path),
        "metric": round(mean_diff, 2),
        "explanation": (
            "Error Level Analysis re-saves the image as JPEG and shows where it "
            "compresses differently. ELA is less reliable for PNGs, scanned PDFs, "
            "and recompressed images, so treat it as weak evidence."
        ),
        "_map": _norm01(diff_gray),
    }


# ---------------------------------------------------------------------------
# C. Edge map (Canny)
# ---------------------------------------------------------------------------
def generate_edge_map(image_path: str | Path, output_dir: str | Path) -> dict:
    """Canny edge map + edge density. Mostly informational context."""
    output_dir = Path(output_dir)
    edge_path = output_dir / "edge_map.png"

    image = _imread_color(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    _imwrite(edge_path, edges)

    density = float((edges > 0).mean())
    score = float(np.clip(density / 0.25, 0.0, 1.0))

    return {
        "name": "Edge density",
        "score": round(score, 3),
        "level": _level_for(score),
        "path": str(edge_path),
        "metric": round(density, 4),
        "explanation": (
            "Edge density measures how much fine detail the page contains. "
            "Documents are naturally edge-rich; this is context, not by itself a "
            "sign of editing."
        ),
        "_map": (edges.astype(np.float32) / 255.0),
    }


# ---------------------------------------------------------------------------
# D. Sharpness / blur map
# ---------------------------------------------------------------------------
def generate_blur_sharpness_map(image_path: str | Path, output_dir: str | Path) -> dict:
    """
    Local sharpness via the magnitude of the Laplacian. Pasted/edited regions
    can be sharper or blurrier than the rest — but focus, scanning, and
    compression also change local sharpness, so this is weak evidence.
    """
    output_dir = Path(output_dir)
    sharp_path = output_dir / "sharpness_map.png"

    image = _imread_color(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    lap_abs = np.abs(lap)
    local = cv2.GaussianBlur(lap_abs, (0, 0), sigmaX=7)

    norm = cv2.normalize(local, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(norm, cv2.COLORMAP_VIRIDIS)
    _imwrite(sharp_path, heat)

    global_var = float(lap.var())
    # Divisor kept high so flat synthetic/clean documents (high text-vs-blank
    # block variance) stay conservative; a genuine localized paste still has
    # headroom to score higher.
    cv_value = _block_cv(local, blocks=8)
    score = float(np.clip(cv_value / 3.5, 0.0, 1.0))

    return {
        "name": "Sharpness inconsistency",
        "score": round(score, 3),
        "level": _level_for(score),
        "path": str(sharp_path),
        "metric": round(global_var, 2),
        "explanation": (
            "Pasted or edited regions can have different sharpness from the rest "
            "of the page. Scanning and focus also cause this, so it is weak "
            "evidence only."
        ),
        "_map": _norm01(local),
    }


# ---------------------------------------------------------------------------
# E. Noise map
# ---------------------------------------------------------------------------
def generate_noise_map(image_path: str | Path, output_dir: str | Path) -> dict:
    """
    Noise residual = grayscale minus a blurred copy (high-frequency content).
    Spliced regions sometimes carry different sensor/scan noise — but WhatsApp
    forwarding, screenshots, and recompression also change noise, so weak only.
    """
    output_dir = Path(output_dir)
    noise_path = output_dir / "noise_map.png"

    image = _imread_color(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=2)
    residual = np.abs(gray - blurred)
    local_noise = cv2.GaussianBlur(residual, (0, 0), sigmaX=9)

    norm = cv2.normalize(local_noise, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(norm, cv2.COLORMAP_MAGMA)
    _imwrite(noise_path, heat)

    mean_noise = float(residual.mean())
    # Same conservative normalization rationale as the sharpness map.
    cv_value = _block_cv(local_noise, blocks=8)
    score = float(np.clip(cv_value / 3.5, 0.0, 1.0))

    return {
        "name": "Noise inconsistency",
        "score": round(score, 3),
        "level": _level_for(score),
        "path": str(noise_path),
        "metric": round(mean_noise, 3),
        "explanation": (
            "Uneven noise across the page can hint at a spliced region. "
            "Compression, scanning, and messaging-app re-encoding also change "
            "noise, so treat this as weak evidence."
        ),
        "_map": _norm01(local_noise),
    }


# ---------------------------------------------------------------------------
# F. Combined anomaly heatmap
# ---------------------------------------------------------------------------
# Weights for combining the weak signals. ELA / sharpness / noise carry most of
# the (still small) weight; edge density is mostly context.
_WEIGHTS = {"ela": 0.30, "edge": 0.10, "sharp": 0.30, "noise": 0.30}
# Dampen the final anomaly so typical clean documents stay conservative.
_ANOMALY_DAMPEN = 0.9


def generate_anomaly_heatmap(
    image_path: str | Path,
    ela_result: dict,
    edge_result: dict,
    blur_result: dict,
    noise_result: dict,
    output_dir: str | Path,
) -> dict:
    """
    Blend the per-pixel weak-signal maps into one heatmap overlaid on the
    document, and combine the per-signal scores into a single conservative
    anomaly score in 0..1.
    """
    output_dir = Path(output_dir)
    heat_path = output_dir / "anomaly_heatmap.png"

    base = _imread_color(image_path)
    h, w = base.shape[:2]

    def _fit(m):
        m = np.asarray(m, dtype=np.float32)
        if m.shape[:2] != (h, w):
            m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
        return m

    combined = (
        _WEIGHTS["ela"] * _fit(ela_result["_map"])
        + _WEIGHTS["edge"] * _fit(edge_result["_map"])
        + _WEIGHTS["sharp"] * _fit(blur_result["_map"])
        + _WEIGHTS["noise"] * _fit(noise_result["_map"])
    )
    combined = _norm01(combined)

    heat_uint8 = (combined * 255).astype(np.uint8)
    heat_color = cv2.applyColorMap(heat_uint8, cv2.COLORMAP_TURBO)

    # Overlay the heatmap on a desaturated copy of the document for context.
    gray_bgr = cv2.cvtColor(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    overlay = cv2.addWeighted(heat_color, 0.55, gray_bgr, 0.45, 0)
    _imwrite(heat_path, overlay)

    anomaly = (
        _WEIGHTS["ela"] * ela_result["score"]
        + _WEIGHTS["edge"] * edge_result["score"]
        + _WEIGHTS["sharp"] * blur_result["score"]
        + _WEIGHTS["noise"] * noise_result["score"]
    )
    anomaly_score = float(np.clip(anomaly * _ANOMALY_DAMPEN, 0.0, 1.0))

    return {"path": str(heat_path), "anomaly_score": round(anomaly_score, 3)}


# ---------------------------------------------------------------------------
# G. Orchestrator
# ---------------------------------------------------------------------------
def _rel_to_root(path: str | Path, project_root: Path) -> str:
    """Return a project-root-relative POSIX path, e.g. forensic_outputs/<id>/ela.png."""
    try:
        return Path(path).resolve().relative_to(project_root.resolve()).as_posix()
    except Exception:
        return Path(path).as_posix()


def _public_signal(s: dict) -> dict:
    """Strip the internal numpy map and the absolute path for the report JSON."""
    return {
        "name": s["name"],
        "score": s["score"],
        "level": s["level"],
        "metric": s.get("metric"),
        "explanation": s["explanation"],
    }


def run_forensics(
    input_file: str | Path,
    case_id: str,
    forensic_root: Optional[str | Path] = None,
) -> dict:
    """
    Run the full forensics pipeline for one case. NEVER raises — on failure it
    returns {"available": false, "error": ...} so the caller keeps going.
    """
    if forensic_root is None:
        from app import config  # local import avoids any import-order issues

        forensic_root = config.FORENSIC_OUTPUTS_DIR
    forensic_root = Path(forensic_root)
    project_root = forensic_root.parent  # forensic_outputs/ lives at project root

    try:
        out_dir, normalized_path = prepare_image_for_forensics(
            input_file, case_id, forensic_root
        )
        ela = generate_ela_image(normalized_path, out_dir)
        edge = generate_edge_map(normalized_path, out_dir)
        blur = generate_blur_sharpness_map(normalized_path, out_dir)
        noise = generate_noise_map(normalized_path, out_dir)
        heat = generate_anomaly_heatmap(normalized_path, ela, edge, blur, noise, out_dir)

        anomaly_score = heat["anomaly_score"]
        risk_contribution = risk_service.forensics_contribution(anomaly_score)

        outputs = {
            "normalized_image": _rel_to_root(normalized_path, project_root),
            "ela_image": _rel_to_root(ela["path"], project_root),
            "edge_map": _rel_to_root(edge["path"], project_root),
            "sharpness_map": _rel_to_root(blur["path"], project_root),
            "noise_map": _rel_to_root(noise["path"], project_root),
            "anomaly_heatmap": _rel_to_root(heat["path"], project_root),
        }

        return {
            "available": True,
            "anomaly_score": round(anomaly_score, 3),
            "risk_contribution": round(risk_contribution, 3),
            "summary": (
                "Weak image-forensics signals generated. Human review required "
                "for interpretation — these are not proof of tampering."
            ),
            "limitations": list(_LIMITATIONS),
            "signals": [_public_signal(s) for s in (ela, edge, blur, noise)],
            "outputs": outputs,
        }
    except Exception as exc:  # noqa: BLE001 - forensics must never crash analysis
        return {
            "available": False,
            "error": str(exc),
            "anomaly_score": 0.0,
            "risk_contribution": 0.0,
            "summary": "Image forensics could not be generated.",
            "limitations": list(_LIMITATIONS),
            "signals": [],
            "outputs": {},
        }
