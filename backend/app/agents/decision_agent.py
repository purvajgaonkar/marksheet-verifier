"""
decision_agent.py
=================

DecisionAgent — aggregates the evidence from the OCR, Metadata, Forensics, and
Rule Validation agents and produces the FINAL recommendation.

It does not invent a new score: it calls the existing risk_service (which
already weighs OCR/metadata/fields and the capped forensics contribution), then
wraps the result in a human-friendly, non-accusatory recommendation.

Allowed final statuses: verified | low | medium | needs_review | high |
unable_to_verify. Never "fraud", "fake", or "forged".
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.services import report_service, risk_service

# Plain-English, non-accusatory recommendation per risk label.
_RECOMMENDATION = {
    "verified": "No tampering signals detected by automated checks. Standard processing can continue.",
    "low": "Low risk signal. Standard processing can continue; no manual review required.",
    "medium": "Some weak signals present. A manual review is recommended before a decision.",
    "needs_review": "Manual review recommended — several weak signals were aggregated.",
    "high": "High risk signal. Prioritise manual review and request official verification.",
    "unable_to_verify": "The document could not be analysed automatically. Request a clearer copy or official verification.",
}

# Labels for which a human reviewer should look at the case.
_HUMAN_REVIEW_LABELS = {"medium", "needs_review", "high", "unable_to_verify"}


class DecisionAgent(BaseAgent):
    name = "Decision Agent"

    def execute(self, context: dict) -> dict:
        metadata_flags = context.get("metadata_flags", {}) or {}
        ocr_result = context.get("ocr_result", {}) or {}
        fields = context.get("fields", {}) or {}
        forensics = context.get("forensics", {}) or {}

        # Reuse the central risk engine (includes the capped forensics signal).
        risk = risk_service.compute_risk(
            metadata_flags, ocr_result, fields, forensics=forensics
        )
        context["risk"] = risk

        label = risk.get("label", "unable_to_verify")
        score = risk.get("score", 0.0)

        # Build a plain-English evidence summary.
        ocr_conf = ocr_result.get("average_confidence")
        flags = metadata_flags.get("flags", [])
        anomaly = forensics.get("anomaly_score") if forensics.get("available") else None
        rv = context.get("rule_validation", {})
        evidence_summary = [
            f"OCR confidence was {ocr_conf}/100."
            if ocr_conf is not None
            else "OCR confidence was unavailable.",
            f"Metadata warnings found: {', '.join(flags)}."
            if flags
            else "No metadata warnings were found.",
            f"Image forensics anomaly score was {anomaly} (weak evidence)."
            if anomaly is not None
            else "Image forensics was not available.",
            f"Rule validation passed {rv.get('rules_passed', '?')} of "
            f"{rv.get('rules_total', '?')} basic checks.",
        ]

        human_review_required = label in _HUMAN_REVIEW_LABELS
        recommendation = _RECOMMENDATION.get(label, _RECOMMENDATION["unable_to_verify"])

        decision = {
            "final_status": label,
            "risk_score": score,
            "risk_label": label,
            "recommendation": recommendation,
            "evidence_summary": evidence_summary,
            "human_review_required": human_review_required,
            "important_note": report_service.MVP_DISCLAIMER,
        }
        context["decision"] = decision

        warnings = []
        if human_review_required:
            warnings.append("Manual human review is recommended for this case.")

        # Confidence here = how settled the recommendation is (display only).
        confidence = 0.3 if label == "unable_to_verify" else round(max(0.0, 1.0 - score), 3)

        return {
            "summary": recommendation,
            "confidence": confidence,
            "findings": evidence_summary,
            "warnings": warnings,
        }
