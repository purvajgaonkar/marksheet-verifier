"""
orchestrator.py
===============

The Orchestrator runs the local rule-based agents in order and aggregates their
outputs into the final report. This is the "agentic" architecture for the MVP —
deterministic, offline, and with NO external AI/LLM API.

Flow:
    1. _prepare()  — CRITICAL input processing (validate file, check tools,
                     render PDF, preprocess image). If this fails, the whole run
                     fails with AnalyzerError (the CLI/API surface a clean error).
    2. Run agents in order, collecting a trace. Weak agents that fail are
       recorded as "failed"/"completed_with_warnings" but the run continues.
           OCR Agent -> Metadata Agent -> Forensics Agent
                     -> Rule Validation Agent -> Decision Agent
    3. Build the `agentic_workflow` block (run_id, timings, trace, recommendation).

The Orchestrator returns a plain dict of pieces; analysis_service turns those
into the report via report_service.build_report (so the report keeps its shape
and old reports stay compatible).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path

from app.agents.decision_agent import DecisionAgent
from app.agents.forensics_agent import ForensicsAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.rule_validation_agent import RuleValidationAgent
from app.services import image_preprocess_service, ocr_service, pdf_service
from app.utils import command_checks

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class AnalyzerError(Exception):
    """
    Raised for CRITICAL failures the caller must handle (missing file,
    unsupported type, missing Tesseract, PDF render / preprocess failure).
    The CLI turns this into a friendly message; the API into an HTTP error.
    """


class Orchestrator:
    """Runs the five local agents and assembles the agentic workflow trace."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        # The fixed agent order. Each is a small, single-responsibility module.
        self.agents = [
            OCRAgent(),
            MetadataAgent(),
            ForensicsAgent(),
            RuleValidationAgent(),
            DecisionAgent(),
        ]

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    # -- Critical input processing (failure aborts the whole run) ----------
    def _prepare(self, input_path: Path, forensic_dir: Path, base_name: str) -> dict:
        if not input_path.exists():
            raise AnalyzerError(f"Input file does not exist: {input_path}")

        extension = input_path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise AnalyzerError(
                f"Unsupported file type '{extension}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        tools = command_checks.check_all_tools()
        tess, exif = tools["tesseract"], tools["exiftool"]
        self._log(
            f"  tools: Tesseract {'OK' if tess['available'] else 'MISSING'}, "
            f"ExifTool {'OK' if exif['available'] else 'MISSING'}"
        )
        if not tess["available"]:
            raise AnalyzerError(
                "Tesseract OCR is required but was not found. "
                f"Detail: {tess.get('error')}."
            )
        ocr_service.configure_tesseract(tess["path"])

        pdf_page_count = None
        if pdf_service.is_pdf(input_path):
            pdf_page_count = pdf_service.get_pdf_page_count(input_path)
            rendered_png = forensic_dir / f"{base_name}__pdf_page1.png"
            try:
                image_for_ocr = pdf_service.render_first_page_to_png(input_path, rendered_png)
            except Exception as exc:  # noqa: BLE001
                raise AnalyzerError(f"Failed to render PDF: {exc}") from exc
        else:
            image_for_ocr = input_path

        try:
            preprocess_info = image_preprocess_service.preprocess_for_ocr(
                image_for_ocr, forensic_dir, base_name
            )
        except Exception as exc:  # noqa: BLE001
            raise AnalyzerError(f"Image preprocessing failed: {exc}") from exc

        return {
            "input_path": input_path,
            "forensic_dir": Path(forensic_dir),
            "base_name": base_name,
            "tools": tools,
            "exiftool_path": exif.get("path"),
            "pdf_page_count": pdf_page_count,
            "preprocess_info": preprocess_info,
        }

    # -- Run the full workflow ---------------------------------------------
    def run(
        self,
        input_path: str | Path,
        *,
        forensic_dir: str | Path,
        base_name: str,
        display_name: str | None = None,
    ) -> dict:
        run_id = "run_" + uuid.uuid4().hex[:12]
        started_at = datetime.now()
        start = time.perf_counter()
        self._log(f"[orchestrator] {run_id} starting (mode=local_rule_based)")

        # Critical prep first — raises AnalyzerError on failure.
        context = self._prepare(Path(input_path), Path(forensic_dir), base_name)
        context["display_name"] = display_name or context["input_path"].name

        # Run each agent; BaseAgent.run never raises, so the loop always finishes.
        trace = []
        for agent in self.agents:
            result = agent.run(context)
            self._log(
                f"  -> {result['agent_name']}: {result['status']} "
                f"({result['duration_ms']} ms) - {result['summary']}"
            )
            trace.append(result)

        completed_at = datetime.now()
        duration_ms = int((time.perf_counter() - start) * 1000)
        decision = context.get("decision", {})

        agentic_workflow = {
            "available": True,
            "run_id": run_id,
            "mode": "local_rule_based",
            "summary": "Local agentic workflow completed.",
            "agents_executed": len(trace),
            "started_at": started_at.isoformat(timespec="seconds"),
            "completed_at": completed_at.isoformat(timespec="seconds"),
            "duration_ms": duration_ms,
            "recommendation": decision,
            "trace": trace,
        }

        # Return the pieces analysis_service needs to build the report. Defaults
        # keep things safe if a weak agent failed and never populated context.
        return {
            "tools": context["tools"],
            "pdf_page_count": context.get("pdf_page_count"),
            "preprocess_info": context["preprocess_info"],
            "ocr_result": context.get(
                "ocr_result", {"text": "", "average_confidence": 0.0, "word_count": 0}
            ),
            "fields": context.get("fields", {}),
            "raw_metadata": context.get("raw_metadata", {}),
            "metadata_flags": context.get(
                "metadata_flags",
                {"flags": [], "details": {}, "metadata_available": False},
            ),
            "forensics": context.get("forensics", {"available": False}),
            "risk": context.get(
                "risk",
                {"score": 1.0, "label": "unable_to_verify", "contributing_factors": []},
            ),
            "agentic_workflow": agentic_workflow,
        }
