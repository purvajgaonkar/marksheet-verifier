"""
db_models.py
============

SQLAlchemy ORM models (Phase 8).

The database stores STRUCTURED case/review/audit data and FILE REFERENCES only.
Uploaded files and JSON reports stay on disk; the DB holds their paths.

Tables:
    users               - students / admins / reviewers
    cases               - one row per uploaded marksheet (mirrors reports/)
    student_submissions - the student-provided details for a case
    review_decisions    - human reviewer decisions on a case (audit-friendly)
    audit_logs          - append-only trail of everything that happened

Note on naming: `Case.case_id` is the public STRING id (e.g. "case_ab12...").
The integer foreign keys on the other tables (also called `case_id` per the
spec) point at `cases.id` (the integer primary key).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    """A student, admin, or reviewer. Auth comes later; passwords are nullable."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    # logical values: "student", "admin", "reviewer"
    role = Column(String(32), default="student", nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable until auth exists
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    cases = relationship(
        "Case", back_populates="student", foreign_keys="Case.student_id"
    )


class Case(Base):
    """One uploaded marksheet and its computed signals + workflow status."""

    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    original_filename = Column(String(512), nullable=True)
    file_path = Column(String(1024), nullable=True)
    report_path = Column(String(1024), nullable=True)

    # student-facing workflow status (safe wording only):
    # submitted | processing | under_review | verified | reupload_required |
    # official_verification_required | closed
    status = Column(String(48), default="submitted", nullable=False)

    # admin-facing risk label (non-accusatory):
    # low_risk | medium_risk | needs_review | high_risk_signal | unable_to_verify
    admin_risk_label = Column(String(48), nullable=True)

    risk_score = Column(Float, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    metadata_flag_count = Column(Integer, nullable=True)
    forensics_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    student = relationship("User", back_populates="cases", foreign_keys=[student_id])
    submission = relationship(
        "StudentSubmission", back_populates="case", uselist=False,
        cascade="all, delete-orphan",
    )
    decisions = relationship(
        "ReviewDecision", back_populates="case",
        order_by="ReviewDecision.created_at", cascade="all, delete-orphan",
    )
    audit_logs = relationship(
        "AuditLog", back_populates="case",
        order_by="AuditLog.created_at", cascade="all, delete-orphan",
    )


class StudentSubmission(Base):
    """The student-provided details that accompany an upload."""

    __tablename__ = "student_submissions"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    student_name = Column(String(255), nullable=True)
    student_email = Column(String(255), nullable=True)
    application_id = Column(String(128), nullable=True)
    board_name = Column(String(128), nullable=True)
    exam_year = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    case = relationship("Case", back_populates="submission")


class ReviewDecision(Base):
    """A human reviewer's decision on a case. The system never auto-decides."""

    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # logical values: approved | needs_more_documents |
    # request_official_verification | rejected_after_manual_review | unable_to_verify
    decision = Column(String(48), nullable=False)
    reviewer_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    case = relationship("Case", back_populates="decisions")
    reviewer = relationship("User")


class AuditLog(Base):
    """Append-only record of actions taken on a case (who/what/when)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    case = relationship("Case", back_populates="audit_logs")
    actor = relationship("User")
