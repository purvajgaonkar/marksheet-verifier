"""
upload_routes.py
================

The admin/generic upload endpoint:

    POST /upload
    -> accepts a PDF/JPG/JPEG/PNG file
    -> runs the SHARED intake pipeline (analyze, save report, index, DB sync)
    -> returns the same summary shape as before

As of Phase 8 the heavy lifting lives in intake_service.run_intake(), which is
also used by the student submission route. The response shape is unchanged so
the existing frontend keeps working.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import UploadResponse
from app.services import intake_service
from app.services.report_service import MVP_DISCLAIMER

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """Accept a marksheet upload, analyze it, persist it, and return a summary."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_bytes = await file.read()

    try:
        result = await intake_service.run_intake(file_bytes, file.filename)
    except intake_service.IntakeError as exc:
        # Bad file type / empty / analysis could not be performed.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - unexpected failure -> 500
        raise HTTPException(
            status_code=500, detail=f"Unexpected analysis error: {exc}"
        ) from exc

    return UploadResponse(
        case_id=result["case_id"],
        filename=file.filename,
        risk_score=result["risk_score"],
        risk_label=result["risk_label"] or "unable_to_verify",
        ocr_confidence=result["ocr_confidence"],
        forensics_anomaly_score=result["forensics_anomaly_score"],
        report_path=result["report_path"],
        disclaimer=MVP_DISCLAIMER,
    )
