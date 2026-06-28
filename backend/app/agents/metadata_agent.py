"""
metadata_agent.py
=================

MetadataAgent — reads file metadata with ExifTool (via the existing
metadata_service) and surfaces warning flags.

Important: a metadata warning is NOT proof of tampering. Scanners, phone
cameras, messaging apps, and ordinary re-saving all change metadata for
innocent reasons. The agent phrases everything as a *possible* signal.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.services import metadata_service


class MetadataAgent(BaseAgent):
    name = "Metadata Agent"

    def execute(self, context: dict) -> dict:
        raw_metadata = metadata_service.extract_metadata(
            context["input_path"], context.get("exiftool_path")
        )
        flags_info = metadata_service.analyze_metadata_flags(raw_metadata)

        context["raw_metadata"] = raw_metadata
        context["metadata_flags"] = flags_info

        flags = flags_info.get("flags", [])
        details = flags_info.get("details", {})
        metadata_available = flags_info.get("metadata_available", False)

        findings = []
        warnings = []

        if not metadata_available:
            warnings.append("File metadata could not be read (this alone is not suspicious).")

        if flags:
            findings.append(f"{len(flags)} metadata warning flag(s): {', '.join(flags)}.")
            for flag in flags:
                warnings.append(details.get(flag, flag.replace("_", " ")))
        else:
            findings.append("No metadata warning flags were raised.")

        summary = (
            "No metadata warnings found."
            if not flags
            else f"{len(flags)} metadata warning(s) found — not proof of tampering."
        )

        return {
            "summary": summary,
            "confidence": 1.0 if metadata_available else 0.3,
            "findings": findings,
            "warnings": warnings,
        }
