"""
health_routes.py
================

A health-check endpoint deployment platforms (and the frontend) can poll to
confirm the server is alive and its dependencies are reachable.

    GET /health
    -> {
         "status": "ok",
         "environment": "development",
         "database": "connected",         # or "error"
         "llm_enabled": false,
         "version": "phase-10",
         "tesseract_available": true,      # kept for backward compatibility
         "exiftool_available": true,
         "tesseract_version": "...",
         "exiftool_version": "..."
       }

No secrets are ever returned (no API key, no JWT secret, no DB URL).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app import config
from app.database import engine
from app.schemas import HealthResponse
from app.utils import command_checks

router = APIRouter(tags=["health"])
logger = logging.getLogger("marksheet.health")

API_VERSION = "phase-10"


def _database_status() -> str:
    """Return 'connected' if a trivial query works, else 'error' (never raises)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as exc:  # noqa: BLE001 - health must never crash
        logger.warning("Health check: database not reachable: %s", exc)
        return "error"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report server status, environment, DB connectivity, and tool availability."""
    tools = command_checks.check_all_tools()
    tess = tools["tesseract"]
    exif = tools["exiftool"]
    return HealthResponse(
        status="ok",
        environment=config.ENVIRONMENT,
        database=_database_status(),
        llm_enabled=config.llm_is_available(),
        version=API_VERSION,
        tesseract_available=tess["available"],
        exiftool_available=exif["available"],
        tesseract_version=tess.get("version"),
        exiftool_version=exif.get("version"),
    )
