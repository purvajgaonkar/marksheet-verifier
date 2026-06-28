"""
schemas package
===============

Pydantic models describing the SHAPE of our API responses/requests.

Phase 9 turned the old single-file `schemas.py` into this package so auth
schemas can live in their own module. Everything is re-exported here, so the
existing `from app.schemas import UploadResponse` style imports keep working,
and `from app.schemas.auth_schemas import UserCreate` works too.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Re-export the auth schemas so `from app.schemas import UserCreate` works.
from app.schemas.auth_schemas import (  # noqa: F401
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


class RootResponse(BaseModel):
    """Returned by GET / ."""
    name: str
    message: str
    docs_url: str
    disclaimer: str


class HealthResponse(BaseModel):
    """Returned by GET /health . Used by deployment platforms to check liveness."""
    status: str = Field(..., examples=["ok"])
    # Phase 10 deployment fields.
    environment: Optional[str] = None
    database: Optional[str] = None  # "connected" | "error"
    llm_enabled: Optional[bool] = None
    version: Optional[str] = None
    # Original Phase 2 fields (kept for backward compatibility).
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


class StudentSubmissionItem(BaseModel):
    """One row in GET /student/my-submissions (safe, no internal risk)."""
    case_id: str
    original_filename: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    action_required: bool = False
    action_message: Optional[str] = None


class AdminDecisionRequest(BaseModel):
    """Body for POST /admin/cases/{case_id}/decision (a human reviewer action)."""
    decision: str
    reviewer_comment: Optional[str] = None
    student_status: str
