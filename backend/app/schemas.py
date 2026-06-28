"""
schemas.py
==========

Pydantic models that describe the SHAPE of our API responses.

These give us two things for free:
    * automatic request/response validation, and
    * a nicely documented interactive API at /docs (Swagger UI).

They are intentionally small and match exactly what the routes return.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Returned by GET / ."""
    name: str
    message: str
    docs_url: str
    disclaimer: str


class HealthResponse(BaseModel):
    """Returned by GET /health ."""
    status: str = Field(..., examples=["ok"])
    tesseract_available: bool
    exiftool_available: bool
    tesseract_version: Optional[str] = None
    exiftool_version: Optional[str] = None


class UploadResponse(BaseModel):
    """Returned by POST /upload ."""
    case_id: str
    filename: str
    risk_score: Optional[float] = None
    risk_label: str
    ocr_confidence: Optional[float] = None
    forensics_anomaly_score: Optional[float] = None
    report_path: str
    disclaimer: str


class CaseSummary(BaseModel):
    """One row in the cases index (returned by /cases and /cases/{id})."""
    case_id: str
    filename: str
    file_type: Optional[str] = None
    sha256: Optional[str] = None
    uploaded_at: Optional[str] = None
    risk_score: Optional[float] = None
    risk_label: Optional[str] = None
    ocr_confidence: Optional[float] = None
    forensics_anomaly_score: Optional[float] = None
    status: Optional[str] = None
    report_path: Optional[str] = None


class CaseListResponse(BaseModel):
    """Returned by GET /cases ."""
    count: int
    cases: list[CaseSummary]


class RagAskRequest(BaseModel):
    """Body for POST /rag/ask ."""
    question: str
    case_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 8: student + admin workflow
# ---------------------------------------------------------------------------
class StudentSubmitResponse(BaseModel):
    """Safe student-facing response for POST /student/submit (no internal risk)."""
    case_id: str
    status: str
    message: str
    submitted_at: str
    next_steps: list[str]


class StudentStatusResponse(BaseModel):
    """Safe student-facing status for GET /student/submission/{case_id}."""
    case_id: str
    status: str
    message: str
    submitted_at: Optional[str] = None
    updated_at: Optional[str] = None
    action_required: bool = False
    action_message: Optional[str] = None


class AdminDecisionRequest(BaseModel):
    """Body for POST /admin/cases/{case_id}/decision (a human reviewer action)."""
    decision: str
    reviewer_comment: Optional[str] = None
    student_status: str
