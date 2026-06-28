"""
student_routes.py
=================

Student-facing endpoints (Phase 8, secured in Phase 9).

    POST /student/submit               -> submit a marksheet (requires student login)
    GET  /student/submission/{case_id} -> track ONE of your own submissions
    GET  /student/my-submissions       -> list YOUR submissions

Security:
    * All routes require an authenticated STUDENT.
    * A student can only see their OWN cases (ownership is enforced).
    * Responses are SAFE: never the risk score, forensics score, metadata
      warnings, agent trace, or AI explanation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import get_db
from app.dependencies.auth_dependencies import require_student
from app.models import db_models as m
from app.schemas import (
    StudentStatusResponse,
    StudentSubmissionItem,
    StudentSubmitResponse,
)
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


def _message_for(status: str):
    return _STATUS_MESSAGES.get(status, _DEFAULT_MESSAGE)


@router.post("/student/submit", response_model=StudentSubmitResponse)
async def student_submit(
    file: UploadFile = File(...),
    application_id: Optional[str] = Form(None),
    board_name: Optional[str] = Form(None),
    exam_year: Optional[str] = Form(None),
    current_user: m.User = Depends(require_student),
) -> StudentSubmitResponse:
    """
    Submit a marksheet (authenticated student). The case is associated with the
    logged-in student. Returns ONLY safe student-facing information.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    file_bytes = await file.read()
    # The student's identity comes from the token; details come from the form.
    student_info = {
        "student_name": current_user.full_name,
        "student_email": current_user.email,
        "application_id": (application_id or "").strip() or None,
        "board_name": (board_name or "").strip() or None,
        "exam_year": (exam_year or "").strip() or None,
    }

    try:
        result = await intake_service.run_intake(
            file_bytes,
            file.filename,
            student_info=student_info,
            student_user_id=current_user.id,
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
            "You can track this submission from 'Track My Submissions'.",
            "The university may request additional verification if required.",
            "You will be asked to re-upload only if a clearer copy is needed.",
        ],
    )


@router.get("/student/my-submissions", response_model=list[StudentSubmissionItem])
def my_submissions(
    current_user: m.User = Depends(require_student), db=Depends(get_db)
) -> list[StudentSubmissionItem]:
    """List the current student's submissions (safe fields only), newest first."""
    cases = (
        db.query(m.Case)
        .filter(m.Case.student_id == current_user.id)
        .order_by(m.Case.created_at.desc())
        .all()
    )
    items = []
    for c in cases:
        _message, action_required, action_message = _message_for(c.status)
        items.append(
            StudentSubmissionItem(
                case_id=c.case_id,
                original_filename=c.original_filename,
                status=c.status,
                created_at=c.created_at.isoformat(timespec="seconds") if c.created_at else None,
                updated_at=c.updated_at.isoformat(timespec="seconds") if c.updated_at else None,
                action_required=action_required,
                action_message=action_message,
            )
        )
    return items


@router.get("/student/submission/{case_id}", response_model=StudentStatusResponse)
def student_submission_status(
    case_id: str,
    current_user: m.User = Depends(require_student),
    db=Depends(get_db),
) -> StudentStatusResponse:
    """Return the SAFE status of ONE of your own submissions. No internal risk."""
    case = persistence_service.get_case(db, case_id)
    # 404 for both "not found" and "not yours" so we never leak another
    # student's case existence.
    if case is None or case.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Submission not found.")

    message, action_required, action_message = _message_for(case.status)
    return StudentStatusResponse(
        case_id=case.case_id,
        status=case.status,
        message=message,
        submitted_at=case.created_at.isoformat(timespec="seconds") if case.created_at else None,
        updated_at=case.updated_at.isoformat(timespec="seconds") if case.updated_at else None,
        action_required=action_required,
        action_message=action_message,
    )
