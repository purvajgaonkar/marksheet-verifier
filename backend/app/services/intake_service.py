"""
intake_service.py
=================

The SHARED intake pipeline for an uploaded marksheet (Phase 8).

Both the existing admin upload (POST /upload) and the new student submission
(POST /student/submit) run through here, so the analysis + report + JSON index +
database sync all happen in exactly one place.

run_intake():
    1. validate the file (type / non-empty),
    2. save the original into uploads/ with a unique case_id,
    3. run the SAME analyzer pipeline (Phases 1-5) in a worker thread,
    4. save the JSON report (Phase 2 flow, unchanged) + cases_index entry,
    5. sync a Case row + StudentSubmission + audit trail into the database.

It raises IntakeError for client problems (bad file type, empty, analysis
failure) so routes can return a clean 400/422.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi.concurrency import run_in_threadpool

from app import config
from app.services import file_storage, persistence_service, report_service
from app.services.analysis_service import AnalyzerError, analyze_file
from app.utils import hashing

# Fresh submissions always start in human-gated review (never auto-verified).
DEFAULT_STATUS = "under_review"


class IntakeError(Exception):
    """A client-side problem with the upload (bad type, empty, analysis failed)."""


def _new_case_id() -> str:
    return "case_" + uuid.uuid4().hex[:12]


async def run_intake(
    file_bytes: bytes,
    original_filename: str,
    *,
    student_info: Optional[dict] = None,
    student_user_id: Optional[int] = None,
) -> dict:
    """
    Process one uploaded file end-to-end. Returns a dict with the case_id, the
    full report, file/report paths, the student-facing status, and the key
    signals (for the admin response). Raises IntakeError on client problems.
    """
    if not original_filename:
        raise IntakeError("No filename provided.")
    extension = Path(original_filename).suffix.lower()
    if extension not in config.SUPPORTED_EXTENSIONS:
        raise IntakeError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(config.SUPPORTED_EXTENSIONS))}"
        )
    if not file_bytes:
        raise IntakeError("Uploaded file is empty.")

    config.ensure_directories()

    case_id = _new_case_id()
    sha256 = hashing.sha256_bytes(file_bytes)

    saved = file_storage.save_upload(
        file_bytes=file_bytes,
        original_filename=original_filename,
        case_id=case_id,
        uploads_dir=config.UPLOADS_DIR,
    )
    stored_path = saved["stored_path"]

    # Run the shared analyzer pipeline in a worker thread (it is CPU-bound).
    try:
        report = await run_in_threadpool(
            analyze_file,
            stored_path,
            forensic_dir=config.FORENSIC_OUTPUTS_DIR,
            base_name=case_id,
            display_name=original_filename,
            verbose=False,
        )
    except AnalyzerError as exc:
        raise IntakeError(str(exc)) from exc

    # Enrich + save the JSON report (unchanged Phase 2 behaviour).
    report["case_id"] = case_id
    report["sha256"] = sha256
    report_path = report_service.save_report(report, config.REPORTS_DIR, case_id)
    report_path_rel = f"reports/{report_path.name}"

    risk = report.get("risk", {})
    ocr = report.get("ocr", {})
    forensics = report.get("image_forensics", {})
    metadata_flags = report.get("metadata", {}).get("flags", []) or []
    forensics_score = forensics.get("anomaly_score") if forensics.get("available") else None

    # Append to the local JSON "database" (unchanged).
    case_entry = {
        "case_id": case_id,
        "filename": original_filename,
        "stored_filename": saved["stored_filename"],
        "file_type": extension.lstrip("."),
        "sha256": sha256,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "risk_score": risk.get("score"),
        "risk_label": risk.get("label"),
        "ocr_confidence": ocr.get("average_confidence"),
        "forensics_anomaly_score": forensics_score,
        "status": "pending_review",
        "report_path": report_path_rel,
    }
    file_storage.add_case(config.CASES_INDEX_PATH, case_entry)

    # Sync the structured row + audit trail into the database (Phase 8).
    status = DEFAULT_STATUS
    persistence_service.sync_intake(
        case_id=case_id,
        original_filename=original_filename,
        file_path=str(stored_path),
        report_path=report_path_rel,
        risk=risk,
        ocr=ocr,
        metadata_flags=metadata_flags,
        forensics_score=forensics_score,
        status=status,
        student_info=student_info,
        student_user_id=student_user_id,
    )

    return {
        "case_id": case_id,
        "report": report,
        "report_path": report_path_rel,
        "status": status,
        "risk_score": risk.get("score"),
        "risk_label": risk.get("label"),
        "ocr_confidence": ocr.get("average_confidence"),
        "forensics_anomaly_score": forensics_score,
        "metadata_flag_count": len(metadata_flags),
    }
