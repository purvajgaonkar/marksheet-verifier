"""
forensic_routes.py
==================

Two read-only endpoints for the Phase 4 image forensics:

    GET /forensics/{case_id}
        -> the list of available forensic output images for a case, as URLs.

    GET /forensic-files/{case_id}/{filename}
        -> serve ONE forensic image file.

Security notes (important — this serves files from disk):
    * Only files inside forensic_outputs/<case_id>/ can be served.
    * Only image extensions (.png, .jpg, .jpeg) are allowed.
    * case_id and filename are sanitised to their bare names, so "..", slashes,
      and absolute paths cannot escape the case folder (no path traversal).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app import config

router = APIRouter(tags=["forensics"])

# The canonical set of forensic outputs, mapping a response key -> filename.
_FORENSIC_FILES = {
    "normalized_image": "normalized.png",
    "ela_image": "ela.png",
    "edge_map": "edge_map.png",
    "sharpness_map": "sharpness_map.png",
    "noise_map": "noise_map.png",
    "anomaly_heatmap": "anomaly_heatmap.png",
}

_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
_MEDIA_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _safe_case_dir(case_id: str) -> Path:
    """
    Resolve forensic_outputs/<case_id>/ and make sure it stays inside the
    forensic outputs root. Returns the resolved directory path (which may not
    exist yet).
    """
    # Strip any directory parts a caller might sneak in.
    safe_id = Path(case_id).name
    root = config.FORENSIC_OUTPUTS_DIR.resolve()
    case_dir = (root / safe_id).resolve()
    # Defence in depth: the resolved dir must be directly under the root.
    if case_dir.parent != root:
        raise HTTPException(status_code=400, detail="Invalid case id.")
    return case_dir


@router.get("/forensics/{case_id}")
def list_forensics(case_id: str, request: Request) -> dict:
    """
    Return the forensic image URLs that exist for a case.

    Response shape:
        {
            "case_id": "...",
            "available": true/false,
            "outputs": { "ela_image": "http://.../forensic-files/<id>/ela.png", ... }
        }
    """
    case_dir = _safe_case_dir(case_id)
    safe_id = Path(case_id).name

    # base_url looks like "http://127.0.0.1:8000/"; strip the trailing slash.
    base = str(request.base_url).rstrip("/")

    outputs: dict[str, str] = {}
    for key, filename in _FORENSIC_FILES.items():
        if (case_dir / filename).is_file():
            outputs[key] = f"{base}/forensic-files/{safe_id}/{filename}"

    return {
        "case_id": safe_id,
        "available": len(outputs) > 0,
        "outputs": outputs,
    }


@router.get("/forensic-files/{case_id}/{filename}")
def serve_forensic_file(case_id: str, filename: str) -> FileResponse:
    """Serve a single forensic image, with strict path/type validation."""
    # Sanitise both parts to their bare names (blocks "..", slashes, drive letters).
    safe_id = Path(case_id).name
    safe_name = Path(filename).name
    if safe_name != filename or safe_id != case_id:
        raise HTTPException(status_code=400, detail="Invalid path.")

    extension = Path(safe_name).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PNG/JPG image files are served.")

    case_dir = _safe_case_dir(case_id)
    file_path = (case_dir / safe_name).resolve()

    # Final containment check: the file must live inside the case folder.
    if case_dir not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid path.")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Forensic image not found.")

    return FileResponse(file_path, media_type=_MEDIA_TYPES[extension])
