"""
init_db.py
==========

Database initialization (Phase 8).

init_db():
    1. Creates all tables (idempotent).
    2. Creates a couple of demo users (admin + reviewer) if they don't exist.
       NOTE: no real passwords are stored — hashed_password stays NULL until a
       proper auth phase is added.
    3. Backfills the database from the existing reports/cases_index.json so that
       cases uploaded BEFORE Phase 8 still appear in the admin dashboard and
       student tracking. This keeps the JSON flow and the DB in sync.

It is called automatically on FastAPI startup, and can also be run directly:

    python -c "import sys; sys.path.insert(0,'backend'); from app.init_db import init_db; init_db()"
"""

from __future__ import annotations

from app.database import Base, engine
from app.models import db_models as m  # noqa: F401 - import registers the tables
from app.services import file_storage, persistence_service
from app import config


def _ensure_user(db, email: str, full_name: str, role: str) -> None:
    existing = db.query(m.User).filter(m.User.email == email).first()
    if existing is None:
        db.add(m.User(email=email, full_name=full_name, role=role))


def _backfill_from_index(db) -> int:
    """
    Import any cases_index.json entries that are not yet in the DB. Old cases get
    a safe student status of 'under_review'. Returns the number of cases added.
    """
    added = 0
    cases = file_storage.load_cases_index(config.CASES_INDEX_PATH)
    for entry in cases:
        case_id = entry.get("case_id")
        if not case_id:
            continue
        if persistence_service.get_case(db, case_id) is not None:
            continue

        stored = entry.get("stored_filename")
        file_path = f"uploads/{stored}" if stored else None
        case = m.Case(
            case_id=case_id,
            original_filename=entry.get("filename"),
            file_path=file_path,
            report_path=entry.get("report_path"),
            status="under_review",  # old cases predate the workflow -> needs review
            admin_risk_label=persistence_service.admin_label_for(entry.get("risk_label")),
            risk_score=entry.get("risk_score"),
            ocr_confidence=entry.get("ocr_confidence"),
            forensics_score=entry.get("forensics_anomaly_score"),
        )
        db.add(case)
        db.flush()
        persistence_service.add_audit(
            db, case.id, "backfilled_from_index", "Imported from cases_index.json"
        )
        added += 1
    return added


def init_db() -> None:
    """Create tables, seed demo users, and backfill existing cases."""
    Base.metadata.create_all(bind=engine)

    with persistence_service.session_scope() as db:
        _ensure_user(db, "admin@demo.local", "Demo Admin", "admin")
        _ensure_user(db, "reviewer@demo.local", "Demo Reviewer", "reviewer")
        _backfill_from_index(db)


if __name__ == "__main__":  # allow `python backend/app/init_db.py` style runs
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    init_db()
    print("Database initialized.")
