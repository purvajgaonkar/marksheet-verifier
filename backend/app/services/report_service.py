"""
report_service.py
=================

Assembles the final analysis REPORT, saves it as nicely-indented JSON, and
prints a short human-friendly summary to the terminal.

The mandatory disclaimer note is added to EVERY report here, in one place, so
it can never be accidentally left out:

    "This is an MVP signal report, not final proof of tampering."
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


# The exact disclaimer text required on every report.
MVP_DISCLAIMER = "This is an MVP signal report, not final proof of tampering."


def build_report(
    *,
    file_name: str,
    file_path: str,
    file_type: str,
    analyzed_at: str,
    tools: dict,
    ocr_result: dict,
    fields: dict,
    metadata_flags: dict,
    risk: dict,
    preprocess_info: dict,
    pdf_page_count: Optional[int] = None,
    raw_metadata: Optional[dict] = None,
    image_forensics: Optional[dict] = None,
    agentic_workflow: Optional[dict] = None,
) -> dict:
    """
    Build the full report dictionary from all the pieces of evidence.

    Keyword-only arguments keep call sites readable (you can see what each
    value is at the call in analyze.py).
    """
    # Keep an OCR text preview short in the main report; full text lives under
    # "ocr" so the frontend can show a preview without dumping a wall of text.
    full_text = ocr_result.get("text", "") or ""
    preview = full_text.strip().replace("\r\n", "\n")
    if len(preview) > 800:
        preview = preview[:800] + " ...[truncated]"

    report = {
        "schema_version": 1,
        "disclaimer": MVP_DISCLAIMER,
        "file": {
            "name": file_name,
            "path": file_path,
            "type": file_type,
            "pdf_page_count": pdf_page_count,
        },
        "analyzed_at": analyzed_at,
        "tools": {
            "tesseract": tools.get("tesseract", {}),
            "exiftool": tools.get("exiftool", {}),
        },
        "risk": {
            "score": risk.get("score"),
            "label": risk.get("label"),
            "contributing_factors": risk.get("contributing_factors", []),
        },
        "ocr": {
            "average_confidence": ocr_result.get("average_confidence"),
            "word_count": ocr_result.get("word_count"),
            "text_preview": preview,
            "full_text": full_text,
        },
        "detected_fields": fields,
        "metadata": {
            "flags": metadata_flags.get("flags", []),
            "flag_details": metadata_flags.get("details", {}),
            "metadata_available": metadata_flags.get("metadata_available", False),
            # Raw metadata can be large; include it but keep it at the bottom.
            "raw": raw_metadata or {},
        },
        "preprocessing": {
            "denoised": preprocess_info.get("denoised"),
            "final_width": preprocess_info.get("width"),
            "final_height": preprocess_info.get("height"),
            "debug_images": preprocess_info.get("steps", {}),
        },
        # Image/pixel forensics (Phase 4). Always present; "available" is False
        # when forensics could not run, so older code/UIs degrade gracefully.
        "image_forensics": image_forensics
        or {
            "available": False,
            "summary": "Image forensics was not run for this report.",
            "anomaly_score": 0.0,
            "risk_contribution": 0.0,
            "limitations": [],
            "signals": [],
            "outputs": {},
        },
        # Agentic workflow trace (Phase 5). "available" is False on older reports
        # / when the orchestrator was not used, so the UI degrades gracefully.
        "agentic_workflow": agentic_workflow
        or {
            "available": False,
            "mode": "local_rule_based",
            "summary": "Agentic workflow was not run for this report.",
            "trace": [],
        },
        "notes": [
            MVP_DISCLAIMER,
            "Risk labels (verified/low/medium/needs_review/high/unable_to_verify) "
            "are automated signals only. A human reviewer makes the final decision.",
            "Metadata and pixel signals can be misleading (scanning, WhatsApp "
            "forwarding, and re-saving all alter files legitimately).",
        ],
    }
    return report


def save_report(report: dict, reports_dir: str | Path, base_name: str) -> Path:
    """
    Save the report as `<base_name>_report.json` inside `reports_dir`.

    JSON is written with indent=2 and ensure_ascii=False so it is easy to read
    and supports non-English characters in marksheets.

    Returns the path to the written file.
    """
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    out_path = reports_dir / f"{base_name}_report.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    return out_path


def print_summary(report: dict, report_path: str | Path) -> None:
    """Print a short, friendly summary of the report to the terminal."""
    risk = report.get("risk", {})
    ocr = report.get("ocr", {})
    fields = report.get("detected_fields", {})
    flags = report.get("metadata", {}).get("flags", [])
    forensics = report.get("image_forensics", {})

    line = "=" * 60
    print("\n" + line)
    print("  MARKSHEET VERIFIER  -  ANALYSIS SUMMARY")
    print(line)
    print(f"  File name        : {report.get('file', {}).get('name')}")
    print(f"  File type        : {report.get('file', {}).get('type')}")
    print(f"  OCR confidence   : {ocr.get('average_confidence')} / 100")
    print(f"  Detected board   : {fields.get('board')}")
    print(f"  Roll/seat number : {fields.get('roll_number') or 'not detected'}")
    print(f"  Total marks      : {fields.get('total_marks') or 'not detected'}")
    print(f"  Percentage       : {fields.get('percentage') or 'not detected'}")
    print(f"  Risk score       : {risk.get('score')}  (0 = clean, 1 = many signals)")
    print(f"  Risk label       : {risk.get('label')}")

    if flags:
        print(f"  Metadata flags   : {', '.join(flags)}")
    else:
        print("  Metadata flags   : none")

    if forensics.get("available"):
        print(f"  Forensics anomaly: {forensics.get('anomaly_score')} "
              f"(weak pixel signal, max +{forensics.get('risk_contribution')} to risk)")
    else:
        print("  Forensics anomaly: not available")

    print(line)
    print(f"  NOTE: {MVP_DISCLAIMER}")
    print(f"  Full report JSON : {report_path}")
    print(line + "\n")
