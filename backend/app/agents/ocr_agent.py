"""
ocr_agent.py
============

OCRAgent — reads text from the preprocessed image and detects simple fields.

It does NOT re-implement OCR; it calls the existing ocr_service. The
preprocessed image is produced by the orchestrator (critical input step) and
handed over in `context["preprocess_info"]`.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.services import ocr_service


class OCRAgent(BaseAgent):
    name = "OCR Agent"

    def execute(self, context: dict) -> dict:
        preprocess_info = context["preprocess_info"]
        ocr_result = ocr_service.extract_text_with_confidence(
            preprocess_info["preprocessed_image"]
        )
        fields = ocr_service.detect_fields(ocr_result["text"])

        # Share results with later agents.
        context["ocr_result"] = ocr_result
        context["fields"] = fields

        confidence = float(ocr_result.get("average_confidence", 0.0))
        word_count = int(ocr_result.get("word_count", 0))

        findings = [
            f"OCR text extracted ({word_count} words).",
            f"OCR confidence score: {confidence} / 100.",
            f"Detected board: {fields.get('board', 'unknown')}.",
        ]
        if fields.get("roll_number"):
            findings.append(f"Possible roll/seat number: {fields['roll_number']}.")
        if fields.get("total_marks"):
            findings.append(f"Possible total marks: {fields['total_marks']}.")
        if fields.get("percentage") is not None:
            findings.append(f"Possible percentage: {fields['percentage']}%.")
        if fields.get("result_keywords"):
            findings.append(f"Result keyword(s): {', '.join(fields['result_keywords'])}.")

        warnings = []
        if word_count == 0:
            warnings.append("No readable text could be extracted from the document.")

        return {
            "summary": f"Extracted text at {confidence}/100 average OCR confidence.",
            "confidence": round(confidence / 100.0, 3),
            "findings": findings,
            "warnings": warnings,
        }
