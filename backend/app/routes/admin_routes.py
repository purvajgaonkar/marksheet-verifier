"""
admin_routes.py
===============

Admin / reviewer endpoints (Phase 8). Detailed but still non-accusatory.

    GET  /admin/cases                    -> list cases (admin fields)
    GET  /admin/cases/{case_id}          -> full case detail (DB + report + history)
    POST /admin/cases/{case_id}/decision -> record a HUMAN reviewer decision
    GET  /admin/cases/{case_id}/audit    -> audit trail for a case

The system never auto-decides — POST .../decision represents a human action.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app import config
from app.database import get_db
from app.models import db_models as m
from app.schemas import AdminDecisionRequest
from app.services import persistence_service

router = APIRouter(tags=["admin"])


def _load_report(case_id: str) -> dict | None:
    """Read the per-case JSON report from disk, or None if missing/unreadable."""
    report_path = config.REPORTS_DIR / f"{case_id}_report.json"
    if not report_path.is_file():
        return None
    try:
        return json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return None


@router.get("/admin/cases")
def list_cases(db=Depends(get_db)) -> dict:
    """List all cases with admin fields, newest first."""
    cases = db.execute(select(m.Case).order_by(m.Case.created_at.desc())).scalars().all()
    return {
        "count": len(cases),
        "cases": [persistence_service.case_to_admin_dict(c) for c in cases],
    }


@router.get("/admin/cases/{case_id}")
def get_case_detail(case_id: str, db=Depends(get_db)) -> dict:
    """Full admin view: DB fields, the JSON report, decisions, and audit logs."""
    case = persistence_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    report = _load_report(case_id)
    return {
        "case": persistence_service.case_to_admin_dict(case),
        "submission": persistence_service.submission_to_dict(case.submission),
        "report": report,
        "agentic_workflow": (report or {}).get("agentic_workflow"),
        "image_forensics": (report or {}).get("image_forensics"),
        "decisions": [persistence_service.decision_to_dict(d) for d in case.decisions],
        "audit_logs": [persistence_service.audit_to_dict(a) for a in case.audit_logs],
    }


@router.post("/admin/cases/{case_id}/decision")
def record_decision(case_id: str, body: AdminDecisionRequest, db=Depends(get_db)) -> dict:
    """Record a reviewer decision and update the student-facing status."""
    case = persistence_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    if body.decision not in persistence_service.REVIEW_DECISIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid decision '{body.decision}'. Allowed: "
                f"{', '.join(sorted(persistence_service.REVIEW_DECISIONS))}"
            ),
        )
    if body.student_status not in persistence_service.STUDENT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid student_status '{body.student_status}'. Allowed: "
                f"{', '.join(sorted(persistence_service.STUDENT_STATUSES))}"
            ),
        )

    persistence_service.record_decision(
        db,
        case=case,
        decision=body.decision,
        reviewer_comment=body.reviewer_comment,
        student_status=body.student_status,
    )
    db.commit()
    db.refresh(case)

    return {
        "case": persistence_service.case_to_admin_dict(case),
        "decisions": [persistence_service.decision_to_dict(d) for d in case.decisions],
    }


@router.get("/admin/cases/{case_id}/audit")
def get_audit(case_id: str, db=Depends(get_db)) -> dict:
    """Return the audit-log entries for a case."""
    case = persistence_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return {
        "case_id": case_id,
        "audit_logs": [persistence_service.audit_to_dict(a) for a in case.audit_logs],
    }
