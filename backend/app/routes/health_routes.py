"""
health_routes.py
================

A simple health-check endpoint. The frontend (and you) can call it to confirm
the server is up AND that the two external tools are reachable.

    GET /health
    -> {
         "status": "ok",
         "tesseract_available": true,
         "exiftool_available": true,
         "tesseract_version": "...",
         "exiftool_version": "..."
       }
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import HealthResponse
from app.utils import command_checks

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report server status and whether Tesseract/ExifTool are available."""
    tools = command_checks.check_all_tools()
    tess = tools["tesseract"]
    exif = tools["exiftool"]
    return HealthResponse(
        status="ok",
        tesseract_available=tess["available"],
        exiftool_available=exif["available"],
        tesseract_version=tess.get("version"),
        exiftool_version=exif.get("version"),
    )
