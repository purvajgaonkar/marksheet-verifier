"""
case_routes.py
==============

Read-only endpoints for browsing cases and reading full reports.

    GET /cases             -> list every case in the index
    GET /cases/{case_id}   -> one case summary
    GET /reports/{case_id} -> the full JSON report for that case

All data comes from the local JSON store (reports/cases_index.json) and the
per-case report files in reports/. No database is involved in this MVP.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app import config
from app.schemas import CaseListResponse, CaseSummary
from app.services import file_storage

router = APIRouter(tags=["cases"])


@router.get("/cases", response_model=CaseListResponse)
def list_cases() -> CaseListResponse:
    """Return all cases currently recorded in cases_index.json."""
    cases = file_storage.load_cases_index(config.CASES_INDEX_PATH)
    # Newest first is the most useful order for a review dashboard.
    cases_sorted = sorted(
        cases, key=lambda c: c.get("uploaded_at", ""), reverse=True
    )
    return CaseListResponse(
        count=len(cases_sorted),
        cases=[CaseSummary(**c) for c in cases_sorted],
    )


@router.get("/cases/{case_id}", response_model=CaseSummary)
def get_case(case_id: str) -> CaseSummary:
    """Return a single case summary by id, or 404 if it does not exist."""
    case = file_storage.get_case(config.CASES_INDEX_PATH, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return CaseSummary(**case)


@router.get("/reports/{case_id}")
def get_report(case_id: str) -> dict:
    """
    Return the FULL JSON report for a case.

    We look the case up first (so an unknown id gives a clean 404), then read
    its report file from reports/.
    """
    case = file_storage.get_case(config.CASES_INDEX_PATH, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    # The report file is always reports/<case_id>_report.json.
    report_path = config.REPORTS_DIR / f"{case_id}_report.json"
    if not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Report file missing for case {case_id} (expected {report_path.name}).",
        )

    try:
        with open(report_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Could not read report for {case_id}: {exc}"
        ) from exc
