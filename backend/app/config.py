"""
config.py
=========

Central configuration for the whole backend: folder locations, supported file
types, and the CORS origins the React frontend will use.

Keeping these in ONE place means the command-line analyzer (analyze.py) and the
FastAPI server use exactly the same paths, so a report created by one is found
by the other.

All paths use pathlib and are absolute, so they work no matter which directory
you launch the program from (important on Windows).
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Folder layout
# ---------------------------------------------------------------------------
# This file lives at: <project>/backend/app/config.py
#   .parent              -> <project>/backend/app
#   .parent.parent       -> <project>/backend
#   .parent.parent.parent-> <project>            (the project root)
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

UPLOADS_DIR = PROJECT_ROOT / "uploads"
REPORTS_DIR = PROJECT_ROOT / "reports"
FORENSIC_OUTPUTS_DIR = PROJECT_ROOT / "forensic_outputs"
# Phase 6: the local policy documents the RAG assistant retrieves from.
DOCS_DIR = PROJECT_ROOT / "docs"

# The tiny local "database": a JSON file listing every case.
CASES_INDEX_PATH = REPORTS_DIR / "cases_index.json"

# ---------------------------------------------------------------------------
# Accepted uploads
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# CORS: which web origins are allowed to call this API from a browser.
# These are the default ports for Vite (5173) and Create-React-App (3000).
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def ensure_directories() -> None:
    """
    Make sure the read/write folders exist. Safe to call many times.
    Called once on server startup and by the CLI.
    """
    for folder in (UPLOADS_DIR, REPORTS_DIR, FORENSIC_OUTPUTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)
