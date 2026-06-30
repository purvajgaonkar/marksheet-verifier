"""
forensics_agent.py
==================

ForensicsAgent — runs the Phase 4 local image/pixel forensics (via the existing
forensics_service) and reports the weak anomaly signals.

Important: pixel forensics are WEAK signals only. Compression, scanning, mobile
capture, screenshots, WhatsApp forwarding, and PDF conversion can all create
false positives. This agent never overclaims.
"""

from __future__ import annotations

from app import config
from app.agents.base_agent import BaseAgent
from app.services import forensics_service


class ForensicsAgent(BaseAgent):
    name = "Forensics Agent"

    def execute(self, context: dict) -> dict:
        # Phase 11: skip the heavy OpenCV forensics when disabled (e.g. on small
        # free-tier hosts where it would starve the CPU and trigger health-check
        # restarts). The rest of the pipeline treats forensics as "unavailable",
        # which is already handled by the risk engine and the decision agent.
        if not config.FORENSICS_ENABLED:
            context["forensics"] = {
                "available": False,
                "skipped": True,
                "reason": "Image forensics is disabled in this environment.",
            }
            return {
                "summary": "Image forensics skipped (disabled in this environment).",
                "confidence": 0.0,
                "findings": [],
                "warnings": [
                    "Pixel forensics is disabled here; OCR, metadata, and rule "
                    "checks still ran. Run locally for the full forensic analysis."
                ],
                "status": "completed_with_warnings",
            }

        forensics = forensics_service.run_forensics(
            context["input_path"],
            context["base_name"],
            forensic_root=context["forensic_dir"],
        )
        context["forensics"] = forensics

        # Forensics is a WEAK agent: if it fails, we warn but do not fail the run.
        if not forensics.get("available"):
            return {
                "summary": "Image forensics could not be generated (skipped).",
                "confidence": 0.0,
                "findings": [],
                "warnings": [f"Forensics unavailable: {forensics.get('error', 'unknown error')}."],
                "status": "completed_with_warnings",
            }

        anomaly = forensics.get("anomaly_score", 0.0)
        findings = [
            f"Combined anomaly score: {anomaly} (weak signal).",
            "Pixel forensics are weak signals only; compression, scanning, and "
            "messaging-app re-encoding can cause false positives.",
        ]
        for signal in forensics.get("signals", []):
            findings.append(f"{signal['name']}: {signal['score']} ({signal['level']}).")
        findings.append(f"{len(forensics.get('outputs', {}))} forensic visualizations generated.")

        # Only raise a (still weak) warning when the anomaly is actually elevated,
        # so a clean document does not look "flagged".
        warnings = []
        if anomaly > 0.5:
            warnings.append(
                f"Elevated anomaly score ({anomaly}); a human may wish to review the "
                f"highlighted regions — this is weak evidence, not proof."
            )

        return {
            "summary": f"Image-forensics anomaly score {anomaly} (weak evidence only).",
            # Deliberately modest: forensics is weak evidence by design.
            "confidence": 0.4,
            "findings": findings,
            "warnings": warnings,
        }
