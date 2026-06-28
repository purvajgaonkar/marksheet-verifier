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

import os
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
# Phase 7: optional Claude API mode.
# ---------------------------------------------------------------------------
# We load environment variables from backend/.env using python-dotenv. Real
# environment variables (already set in the shell) take precedence over the
# file, which is the standard, safe behaviour.
#
# IMPORTANT: the API key is read from the environment only. It is NEVER
# hardcoded here and NEVER printed/exposed by the API.
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
except Exception:  # noqa: BLE001 - dotenv is optional; missing it just means no .env
    pass


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse a boolean-ish env string safely ('true'/'1'/'yes'/'on' -> True)."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


ANTHROPIC_API_KEY = (os.getenv("ANTHROPIC_API_KEY", "") or "").strip()
# Default to a current, valid model. (The older "claude-3-5-sonnet-latest" alias
# is retired and returns 404; claude-sonnet-4-6 is its current equivalent.)
ANTHROPIC_MODEL = (os.getenv("ANTHROPIC_MODEL", "") or "").strip() or "claude-sonnet-4-6"
LLM_ENABLED = _parse_bool(os.getenv("LLM_ENABLED"), default=False)

try:
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "900"))
except (TypeError, ValueError):
    LLM_MAX_TOKENS = 900

# A placeholder value should count as "no key" so the example file is harmless.
if ANTHROPIC_API_KEY in {"", "your_anthropic_api_key_here"}:
    ANTHROPIC_API_KEY = ""


def llm_is_available() -> bool:
    """
    True only when BOTH the master switch is on AND a non-empty API key exists.
    When False, the app uses the local retrieval fallback (Phase 6).
    """
    return bool(LLM_ENABLED and ANTHROPIC_API_KEY)

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
