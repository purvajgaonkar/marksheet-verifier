"""
database.py
===========

SQLAlchemy database layer (Phase 8).

  * Reads DATABASE_URL from config (default: local SQLite file).
  * Creates the engine and a SessionLocal factory.
  * Exposes the declarative Base that the models inherit from.
  * Provides the get_db() FastAPI dependency (a request-scoped session).

SQLite needs check_same_thread=False because FastAPI may touch the connection
from different threads (e.g. run_in_threadpool). PostgreSQL ignores that arg.

The app keeps storing uploaded files and JSON reports on disk; the database only
stores STRUCTURED metadata and the file paths/references — never raw bytes.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config

DATABASE_URL = config.DATABASE_URL

# SQLite-specific connection arg; harmless to compute, only applied for sqlite.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

# expire_on_commit=False keeps ORM objects usable after commit(), which makes
# returning data from routes simpler.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# All ORM models inherit from this Base.
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
