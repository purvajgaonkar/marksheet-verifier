"""
analysis_service.py
===================

The SHARED analysis entry point used by BOTH:
    * the command-line tool  (backend/analyze.py)        -> Phase 1
    * the FastAPI upload route (app/routes/upload_routes) -> Phase 2

As of Phase 5, the actual work is done by the local rule-based **Orchestrator**
(app/agents/orchestrator.py), which runs the OCR / Metadata / Forensics /
Rule-Validation / Decision agents and produces an `agentic_workflow` trace.

`analyze_file()` is a thin wrapper: it runs the orchestrator and then asks
report_service to shape the pieces into the final report dict. The report keeps
the same structure as before (so older code and the frontend still work), with
the new `agentic_workflow` section added.

`AnalyzerError` is re-exported here so existing imports
(`from app.services.analysis_service import AnalyzerError`) keep working.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agents.orchestrator import (  # re-exported for backward compatibility
    SUPPORTED_EXTENSIONS,
    AnalyzerError,
    Orchestrator,
)
from app.services import report_service

__all__ = ["analyze_file", "AnalyzerError", "SUPPORTED_EXTENSIONS"]


def analyze_file(
    input_path: str | Path,
    *,
    forensic_dir: str | Path,
    base_name: Optional[str] = None,
    display_name: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Run the full agentic analysis pipeline on a single file and return a report.

    Parameters
    ----------
    input_path  : the file on disk to analyze (PDF / JPG / JPEG / PNG).
    forensic_dir: folder where intermediate/forensic images are written.
    base_name   : prefix for the per-case images. Defaults to the file's stem.
                  (The API passes the case_id so files never collide.)
    display_name: the name recorded in the report as the original file name.
                  Defaults to the input file's name.
    verbose     : when True, the orchestrator prints step-by-step progress.

    Returns
    -------
    dict : the full report (see report_service.build_report), now including the
           `agentic_workflow` trace.

    Raises
    ------
    AnalyzerError : for missing files, unsupported types, a missing Tesseract
                    install, or PDF/preprocess failures (critical input steps).
    """
    input_path = Path(input_path)
    base_name = base_name or input_path.stem
    display = display_name or input_path.name
    extension = input_path.suffix.lower()

    orchestrator = Orchestrator(verbose=verbose)
    pieces = orchestrator.run(
        input_path,
        forensic_dir=forensic_dir,
        base_name=base_name,
        display_name=display,
    )

    report = report_service.build_report(
        file_name=display,
        file_path=str(input_path.resolve()),
        file_type=extension.lstrip("."),
        analyzed_at=datetime.now().isoformat(timespec="seconds"),
        tools=pieces["tools"],
        ocr_result=pieces["ocr_result"],
        fields=pieces["fields"],
        metadata_flags=pieces["metadata_flags"],
        risk=pieces["risk"],
        preprocess_info=pieces["preprocess_info"],
        pdf_page_count=pieces["pdf_page_count"],
        raw_metadata=pieces["raw_metadata"],
        image_forensics=pieces["forensics"],
        agentic_workflow=pieces["agentic_workflow"],
    )
    return report
