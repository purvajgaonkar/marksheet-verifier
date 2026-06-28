"""
upload_routes.py
================

The main endpoint of Phase 2:

    POST /upload
    -> accepts a PDF/JPG/JPEG/PNG file
    -> saves the original into uploads/
    -> generates a unique case_id and a SHA-256 hash
    -> runs the SAME analyzer pipeline as the command-line tool
    -> saves the JSON report into reports/<case_id>_report.json
    -> records the case in reports/cases_index.json
    -> returns a short summary

The heavy work (OCR, image processing) runs in a worker thread via
run_in_threadpool so a slow analysis does not freeze the whole server.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app import config
from app.schemas import UploadResponse
from app.services import file_storage, report_service
from app.services.analysis_service import AnalyzerError, analyze_file
from app.services.report_service import MVP_DISCLAIMER
from app.utils import hashing

router = APIRouter(tags=["upload"])


def _new_case_id() -> str:
    """Generate a short, unique, human-friendly case id."""
    return "case_" + uuid.uuid4().hex[:12]


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """Accept a marksheet upload, analyze it, and return a summary."""
    # --- Validate the file name and extension ----------------------------
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    extension = Path(file.filename).suffix.lower()
    if extension not in config.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{extension}'. "
                f"Supported types: {', '.join(sorted(config.SUPPORTED_EXTENSIONS))}"
            ),
        )

    # --- Read the bytes and reject empty uploads -------------------------
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    config.ensure_directories()

    # --- Identity: case id + content hash --------------------------------
    case_id = _new_case_id()
    sha256 = hashing.sha256_bytes(file_bytes)

    # --- Save the original upload ----------------------------------------
    saved = file_storage.save_upload(
        file_bytes=file_bytes,
        original_filename=file.filename,
        case_id=case_id,
        uploads_dir=config.UPLOADS_DIR,
    )
    stored_path = saved["stored_path"]

    # --- Run the shared analyzer pipeline (in a worker thread) -----------
    try:
        report = await run_in_threadpool(
            analyze_file,
            stored_path,
            forensic_dir=config.FORENSIC_OUTPUTS_DIR,
            base_name=case_id,            # keeps debug images unique per case
            display_name=file.filename,   # show the student's original name
            verbose=False,
        )
    except AnalyzerError as exc:
        # A tool is missing or the file could not be analyzed: 422 (the request
        # was understood but could not be processed).
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - unexpected failure -> 500
        raise HTTPException(
            status_code=500, detail=f"Unexpected analysis error: {exc}"
        ) from exc

    # --- Enrich the report with case identity, then save it --------------
    report["case_id"] = case_id
    report["sha256"] = sha256
    report_path = report_service.save_report(report, config.REPORTS_DIR, case_id)

    # --- Record the case in the local JSON "database" --------------------
    risk = report.get("risk", {})
    ocr = report.get("ocr", {})
    forensics = report.get("image_forensics", {})
    forensics_score = forensics.get("anomaly_score") if forensics.get("available") else None
    case_entry = {
        "case_id": case_id,
        "filename": file.filename,
        "stored_filename": saved["stored_filename"],
        "file_type": extension.lstrip("."),
        "sha256": sha256,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "risk_score": risk.get("score"),
        "risk_label": risk.get("label"),
        "ocr_confidence": ocr.get("average_confidence"),
        "forensics_anomaly_score": forensics_score,
        # Reviewer status (used by the Phase 3 dashboard). Starts as pending.
        "status": "pending_review",
        "report_path": f"reports/{report_path.name}",
    }
    file_storage.add_case(config.CASES_INDEX_PATH, case_entry)

    # --- Return the summary ----------------------------------------------
    return UploadResponse(
        case_id=case_id,
        filename=file.filename,
        risk_score=risk.get("score"),
        risk_label=risk.get("label", "unable_to_verify"),
        ocr_confidence=ocr.get("average_confidence"),
        forensics_anomaly_score=forensics_score,
        report_path=case_entry["report_path"],
        disclaimer=MVP_DISCLAIMER,
    )
