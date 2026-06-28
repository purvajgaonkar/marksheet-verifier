"""
student_routes.py
=================

Student-facing endpoints (Phase 8). These are deliberately SAFE: a student never
sees the internal risk score, forensics score, metadata warnings, agent trace, or
the AI explanation. They only see a friendly workflow status and next steps.

    POST /student/submit               -> submit a marksheet (+ optional details)
    GET  /student/submission/{case_id} -> track a submission's status
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.schemas import StudentStatusResponse, StudentSubmitResponse
from app.services import intake_service, persistence_service

router = APIRouter(tags=["student"])

# Safe, student-facing message + action for each workflow status.
_STATUS_MESSAGES = {
    "submitted": ("Your marksheet was received and is queued for processing.", False, None),
    "processing": ("Your marksheet is being processed.", False, None),
    "under_review": ("Your marksheet is under review by the admissions team.", False, None),
    "verified": ("Your marksheet has been verified.", False, None),
    "reupload_required": (
        "A clearer copy is needed.",
        True,
        "Please re-upload a clearer scan or photo of your marksheet.",
    ),
    "official_verification_required": (
        "Additional official verification is required.",
        True,
        "The university may contact your board / DigiLocker to confirm this document.",
    ),
    "closed": ("This submission has been closed.", False, None),
}

_DEFAULT_MESSAGE = ("Your submission status will appear here.", False, None)


def _safe_status_payload(case) -> dict:
    message, action_required, action_message = _STATUS_MESSAGES.get(
        case.status, _DEFAULT_MESSAGE
    )
    return {
        "case_id": case.case_id,
        "status": case.status,
        "message": message,
        "submitted_at": case.created_at.isoformat(timespec="seconds") if case.created_at else None,
        "updated_at": case.updated_at.isoformat(timespec="seconds") if case.updated_at else None,
        "action_required": action_required,
        "action_message": action_message,
    }


@router.post("/student/submit", response_model=StudentSubmitResponse)
async def student_submit(
    file: UploadFile = File(...),
    student_name: Optional[str] = Form(None),
    student_email: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    board_name: Optional[str] = Form(None),
    exam_year: Optional[str] = Form(None),
) -> StudentSubmitResponse:
    """
    Submit a marksheet. Runs the full analysis pipeline behind the scenes and
    records a case, but returns ONLY safe student-facing information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    file_bytes = await file.read()
    student_info = {
        "student_name": (student_name or "").strip() or None,
        "student_email": (student_email or "").strip() or None,
        "application_id": (application_id or "").strip() or None,
        "board_name": (board_name or "").strip() or None,
        "exam_year": (exam_year or "").strip() or None,
    }

    try:
        result = await intake_service.run_intake(
            file_bytes, file.filename, student_info=student_info
        )
    except intake_service.IntakeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Could not process submission: {exc}") from exc

    return StudentSubmitResponse(
        case_id=result["case_id"],
        status=result["status"],
        message="Your marksheet was submitted successfully and is being reviewed.",
        submitted_at=datetime.now().isoformat(timespec="seconds"),
        next_steps=[
            "Save your submission ID to track your status.",
            "The university may request additional verification if required.",
            "You will be asked to re-upload only if a clearer copy is needed.",
        ],
    )


@router.get("/student/submission/{case_id}", response_model=StudentStatusResponse)
def student_submission_status(case_id: str, db=Depends(get_db)) -> StudentStatusResponse:
    """Return the SAFE status of a submission. No internal risk details."""
    case = persistence_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Submission not found.")
    return StudentStatusResponse(**_safe_status_payload(case))
