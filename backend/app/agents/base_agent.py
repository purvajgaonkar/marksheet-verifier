"""
base_agent.py
=============

Shared base class for every local agent in the Phase 5 "agentic" workflow.

Each agent does ONE job (OCR, metadata, forensics, rule validation, decision)
by reusing the existing services. BaseAgent handles the boring-but-important
bits so every agent returns the SAME standard result envelope:

    {
        "agent_name": "OCR Agent",
        "status": "completed",            # see STATUSES below
        "started_at": "2026-...T..:..:..",
        "completed_at": "2026-...T..:..:..",
        "duration_ms": 123,
        "summary": "...",
        "confidence": 0.0,                 # 0..1, the agent's own confidence
        "findings": [ "..." ],
        "warnings": [ "..." ],
        "errors":   [ "..." ],
    }

There is no LLM or external API involved — these "agents" are plain Python
modules with deterministic, explainable logic.
"""

from __future__ import annotations

import time
from datetime import datetime

# Allowed status values for an agent result.
STATUSES = (
    "pending",
    "running",
    "completed",
    "completed_with_warnings",
    "failed",
    "skipped",
)

# Keys an agent's execute() may return to fill the standard envelope.
_ENVELOPE_KEYS = ("summary", "confidence", "findings", "warnings", "errors")


class BaseAgent:
    """
    Subclass this and implement `execute(context)`.

    `execute` may:
      * read shared data from `context` (a plain dict),
      * write its produced data back into `context` (e.g. context["ocr_result"]),
      * return a partial result dict with any of: summary, confidence, findings,
        warnings, errors, status.

    BaseAgent.run() wraps execute() with timing, the standard envelope, and
    error handling, so a misbehaving agent never crashes the whole workflow —
    it is recorded as "failed" and the orchestrator moves on.
    """

    name = "Agent"

    def execute(self, context: dict) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError

    def run(self, context: dict) -> dict:
        result = {
            "agent_name": self.name,
            "status": "running",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": None,
            "duration_ms": 0,
            "summary": "",
            "confidence": 0.0,
            "findings": [],
            "warnings": [],
            "errors": [],
        }

        start = time.perf_counter()
        try:
            out = self.execute(context) or {}
            for key in _ENVELOPE_KEYS:
                if out.get(key) is not None:
                    result[key] = out[key]

            # Decide the final status.
            if result["errors"]:
                result["status"] = "failed"
            elif out.get("status") in STATUSES:
                result["status"] = out["status"]
            elif result["warnings"]:
                result["status"] = "completed_with_warnings"
            else:
                result["status"] = "completed"
        except Exception as exc:  # noqa: BLE001 - an agent must never crash the run
            result["status"] = "failed"
            result["errors"] = list(result["errors"]) + [str(exc)]
            if not result["summary"]:
                result["summary"] = f"{self.name} failed to complete."
        finally:
            result["completed_at"] = datetime.now().isoformat(timespec="seconds")
            result["duration_ms"] = int((time.perf_counter() - start) * 1000)

        return result
