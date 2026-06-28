"""
persistence_service.py
======================

Database helpers (Phase 8). Keeps the SQLAlchemy details in one place so routes
and the intake pipeline stay readable.

Design notes:
    * The JSON report flow (reports/*.json, cases_index.json) is UNCHANGED — the
      database is an ADDITIONAL structured store that mirrors case metadata.
    * Student-facing statuses use safe wording only.
    * The system never auto-decides; decisions are recorded human actions.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from sqlalchemy import select

from app.database import SessionLocal
from app.models import db_models as m

# ---------------------------------------------------------------------------
# Label / status vocabulary
# ---------------------------------------------------------------------------
# Internal risk label (from risk_service) -> admin-facing, non-accusatory label.
_ADMIN_LABEL_MAP = {
    "verified": "low_risk",
    "low": "low_risk",
    "medium": "medium_risk",
    "needs_review": "needs_review",
    "high": "high_risk_signal",
    "unable_to_verify": "unable_to_verify",
}

# The only student-facing statuses we will ever store/return.
STUDENT_STATUSES = {
    "submitted",
    "processing",
    "under_review",
    "verified",
    "reupload_required",
    "official_verification_required",
    "closed",
}

# Allowed reviewer decisions.
REVIEW_DECISIONS = {
    "approved",
    "needs_more_documents",
    "request_official_verification",
    "rejected_after_manual_review",
    "unable_to_verify",
}


def admin_label_for(internal_risk_label: Optional[str]) -> Optional[str]:
    if not internal_risk_label:
        return None
    return _ADMIN_LABEL_MAP.get(internal_risk_label, internal_risk_label)


@contextmanager
def session_scope():
    """A transactional session for callers that are not using Depends(get_db)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------
def get_case(db, case_id: str) -> Optional[m.Case]:
    return db.execute(select(m.Case).where(m.Case.case_id == case_id)).scalar_one_or_none()


def add_audit(db, case_pk: Optional[int], action: str, details: Optional[str] = None,
              actor_user_id: Optional[int] = None) -> None:
    db.add(
        m.AuditLog(
            case_id=case_pk, actor_user_id=actor_user_id, action=action, details=details
        )
    )


def get_or_create_student(db, email: Optional[str], full_name: Optional[str]) -> Optional[m.User]:
    """Find or create a 'student' user by email. Returns None if no email given."""
    if not email:
        return None
    user = db.execute(select(m.User).where(m.User.email == email)).scalar_one_or_none()
    if user is None:
        user = m.User(email=email, full_name=full_name, role="student")
        db.add(user)
        db.flush()
    return user


# ---------------------------------------------------------------------------
# Intake sync (called from the upload pipeline)
# ---------------------------------------------------------------------------
def sync_intake(
    *,
    case_id: str,
    original_filename: str,
    file_path: str,
    report_path: str,
    risk: dict,
    ocr: dict,
    metadata_flags: list,
    forensics_score: Optional[float],
    status: str,
    student_info: Optional[dict] = None,
) -> str:
    """
    Create/update the Case row for a fresh upload, link a StudentSubmission and
    student user if details were provided, and write the audit trail. Returns
    the stored status. Opens and commits its own session.
    """
    with session_scope() as db:
        case = get_case(db, case_id)
        if case is None:
            case = m.Case(case_id=case_id)
            db.add(case)

        case.original_filename = original_filename
        case.file_path = file_path
        case.report_path = report_path
        case.risk_score = risk.get("score")
        case.admin_risk_label = admin_label_for(risk.get("label"))
        case.ocr_confidence = ocr.get("average_confidence")
        case.metadata_flag_count = len(metadata_flags or [])
        case.forensics_score = forensics_score
        case.status = status

        # Link a student user + submission record when student details exist.
        if student_info:
            student = get_or_create_student(
                db, student_info.get("student_email"), student_info.get("student_name")
            )
            if student is not None:
                case.student_id = student.id
            db.flush()  # ensure case.id exists for the FK
            submission = case.submission or m.StudentSubmission(case_id=case.id)
            submission.student_name = student_info.get("student_name")
            submission.student_email = student_info.get("student_email")
            submission.application_id = student_info.get("application_id")
            submission.board_name = student_info.get("board_name")
            submission.exam_year = student_info.get("exam_year")
            if submission.id is None:
                db.add(submission)

        db.flush()  # ensure case.id for the audit rows

        # Audit trail for the upload lifecycle.
        actor_id = case.student_id
        add_audit(db, case.id, "document_uploaded", f"file={original_filename}", actor_id)
        add_audit(db, case.id, "analysis_started", None, actor_id)
        add_audit(
            db, case.id, "analysis_completed",
            f"risk_label={risk.get('label')} risk_score={risk.get('score')} "
            f"ocr={ocr.get('average_confidence')} flags={len(metadata_flags or [])}",
            actor_id,
        )
        add_audit(db, case.id, "status_updated", f"status={status}", actor_id)

    return status


# ---------------------------------------------------------------------------
# Reviewer decision (human action)
# ---------------------------------------------------------------------------
def record_decision(
    db,
    *,
    case: m.Case,
    decision: str,
    reviewer_comment: Optional[str],
    student_status: str,
    reviewer_id: Optional[int] = None,
) -> m.ReviewDecision:
    """Record a reviewer decision, update the case status, and audit it."""
    review = m.ReviewDecision(
        case_id=case.id,
        reviewer_id=reviewer_id,
        decision=decision,
        reviewer_comment=reviewer_comment,
    )
    db.add(review)

    previous = case.status
    case.status = student_status

    add_audit(
        db, case.id, "review_decision",
        f"decision={decision}; comment={(reviewer_comment or '').strip()[:300]}",
        reviewer_id,
    )
    add_audit(
        db, case.id, "status_updated", f"status={previous} -> {student_status}", reviewer_id
    )
    db.flush()
    return review


# ---------------------------------------------------------------------------
# Serialisation helpers (DB row -> plain dict)
# ---------------------------------------------------------------------------
def _iso(dt) -> Optional[str]:
    return dt.isoformat(timespec="seconds") if dt else None


def case_to_admin_dict(case: m.Case) -> dict:
    """Admin/reviewer view of a case (detailed, but non-accusatory)."""
    return {
        "case_id": case.case_id,
        "filename": case.original_filename,
        "file_path": case.file_path,
        "report_path": case.report_path,
        "status": case.status,
        "admin_risk_label": case.admin_risk_label,
        # `risk_label` mirrors admin_risk_label for frontend badge compatibility.
        "risk_label": case.admin_risk_label,
        "risk_score": case.risk_score,
        "ocr_confidence": case.ocr_confidence,
        "metadata_flag_count": case.metadata_flag_count,
        "forensics_score": case.forensics_score,
        "student_id": case.student_id,
        "created_at": _iso(case.created_at),
        "updated_at": _iso(case.updated_at),
        # `uploaded_at` alias keeps the existing CaseTable component working.
        "uploaded_at": _iso(case.created_at),
    }


def submission_to_dict(sub: Optional[m.StudentSubmission]) -> Optional[dict]:
    if sub is None:
        return None
    return {
        "student_name": sub.student_name,
        "student_email": sub.student_email,
        "application_id": sub.application_id,
        "board_name": sub.board_name,
        "exam_year": sub.exam_year,
        "created_at": _iso(sub.created_at),
    }


def decision_to_dict(d: m.ReviewDecision) -> dict:
    return {
        "id": d.id,
        "decision": d.decision,
        "reviewer_comment": d.reviewer_comment,
        "reviewer_id": d.reviewer_id,
        "created_at": _iso(d.created_at),
    }


def audit_to_dict(a: m.AuditLog) -> dict:
    return {
        "id": a.id,
        "action": a.action,
        "details": a.details,
        "actor_user_id": a.actor_user_id,
        "created_at": _iso(a.created_at),
    }
