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


def _parse_csv(value: str | None) -> list[str]:
    """Split a comma-separated env string into a clean list (no empties)."""
    return [part.strip() for part in (value or "").split(",") if part.strip()]


# ---------------------------------------------------------------------------
# Phase 10: deployment environment.
# ---------------------------------------------------------------------------
# ENVIRONMENT switches a few safety behaviours (e.g. CORS strictness and whether
# error responses include details). FRONTEND_URL / BACKEND_URL are the public
# URLs once deployed; locally they default to the Vite / uvicorn dev addresses.
ENVIRONMENT = (os.getenv("ENVIRONMENT", "") or "").strip().lower() or "development"
IS_PRODUCTION = ENVIRONMENT == "production"

FRONTEND_URL = (os.getenv("FRONTEND_URL", "") or "").strip() or "http://localhost:5173"
BACKEND_URL = (os.getenv("BACKEND_URL", "") or "").strip() or "http://127.0.0.1:8000"


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
# Phase 8: database connection.
# ---------------------------------------------------------------------------
# Default to a local SQLite file at the project root so it works no matter
# which directory the server is launched from. Override with DATABASE_URL to
# use PostgreSQL (the app is PostgreSQL-ready).
_DEFAULT_DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / 'marksheet_verifier.db').as_posix()}"
DATABASE_URL = (os.getenv("DATABASE_URL", "") or "").strip() or _DEFAULT_DATABASE_URL


# ---------------------------------------------------------------------------
# Phase 9: authentication (JWT).
# ---------------------------------------------------------------------------
# The default secret is fine for LOCAL development only. For any real
# deployment, set a long random JWT_SECRET_KEY in the environment / .env.
JWT_SECRET_KEY = (os.getenv("JWT_SECRET_KEY", "") or "").strip() or "dev-insecure-change-me"
JWT_ALGORITHM = (os.getenv("JWT_ALGORITHM", "") or "").strip() or "HS256"

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
except (TypeError, ValueError):
    ACCESS_TOKEN_EXPIRE_MINUTES = 120

# ---------------------------------------------------------------------------
# Phase 10: one-time first-admin bootstrap secret.
# ---------------------------------------------------------------------------
# Used by POST /auth/setup-admin to create the very first admin after a fresh
# deployment (when create_admin.py is not available). Read from the environment
# only; the placeholder value counts as "unset" so the endpoint stays disabled.
SETUP_SECRET = (os.getenv("SETUP_SECRET", "") or "").strip()
if SETUP_SECRET in {"change_this_to_a_long_random_setup_secret"}:
    SETUP_SECRET = ""


def setup_admin_enabled() -> bool:
    """True only when a non-empty SETUP_SECRET is configured."""
    return bool(SETUP_SECRET)


# ---------------------------------------------------------------------------
# Accepted uploads (Phase 10: configurable size + extensions)
# ---------------------------------------------------------------------------
try:
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
except (TypeError, ValueError):
    MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

_DEFAULT_UPLOAD_EXTENSIONS = ".pdf,.png,.jpg,.jpeg"


def _parse_ext_set(raw: str | None) -> set[str]:
    """Parse '.pdf,.png' (or 'pdf, png') into a normalised set {'.pdf', '.png'}."""
    out: set[str] = set()
    for part in (raw or "").split(","):
        p = part.strip().lower()
        if not p:
            continue
        if not p.startswith("."):
            p = "." + p
        out.add(p)
    return out


ALLOWED_UPLOAD_EXTENSIONS = (
    _parse_ext_set(os.getenv("ALLOWED_UPLOAD_EXTENSIONS", _DEFAULT_UPLOAD_EXTENSIONS))
    or _parse_ext_set(_DEFAULT_UPLOAD_EXTENSIONS)
)
# Backward-compatible alias (older modules import SUPPORTED_EXTENSIONS).
SUPPORTED_EXTENSIONS = ALLOWED_UPLOAD_EXTENSIONS

# ---------------------------------------------------------------------------
# CORS: which web origins may call this API from a browser.
# Origins come from FRONTEND_URL (comma-separated). In development we also allow
# the common local dev ports. We NEVER use a wildcard ("*") in production.
# ---------------------------------------------------------------------------
_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_frontend_origins = _parse_csv(FRONTEND_URL)

if IS_PRODUCTION:
    # Restrict strictly to the configured frontend URL(s).
    ALLOWED_ORIGINS = _frontend_origins or _DEV_ORIGINS
else:
    # Development: configured origins + local dev ports, de-duplicated, order-kept.
    ALLOWED_ORIGINS = list(dict.fromkeys(_frontend_origins + _DEV_ORIGINS))


def ensure_directories() -> None:
    """
    Make sure the read/write folders exist. Safe to call many times.
    Called once on server startup and by the CLI.
    """
    for folder in (UPLOADS_DIR, REPORTS_DIR, FORENSIC_OUTPUTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)
