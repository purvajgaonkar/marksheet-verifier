"""
metadata_service.py
===================

File metadata extraction and warning-flag analysis using ExifTool.

What is "metadata"?
-------------------
Every file carries hidden information about how it was made: which software
created it, when it was created, when it was last modified, the PDF "producer",
camera details for photos, and so on. ExifTool reads all of that.

Why do we care for tamper signals?
-----------------------------------
A genuine marksheet is usually a scan or an official PDF export. If the
metadata says the file was last touched by "Adobe Photoshop" or "Canva", or if
the created/modified dates disagree, that is a *weak signal* worth a human
glance. It is NOT proof of anything — people legitimately re-save files, and
scanners/phone apps add their own software tags too.

This module:
    1. Runs `exiftool -json <file>` and parses the result.
    2. Looks through the metadata for known image/PDF editors and date issues.
    3. Returns a list of plain-English warning flags.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional


def extract_metadata(file_path: str | Path, exiftool_path: Optional[str]) -> dict:
    """
    Run ExifTool on `file_path` and return the parsed metadata as a dict.

    Parameters
    ----------
    file_path : the file to inspect (PDF or image).
    exiftool_path : absolute path to exiftool.exe (from command_checks). If
                    None, we try the bare name "exiftool" and hope it is on PATH.

    Returns
    -------
    dict of metadata fields. If ExifTool cannot run, returns a dict with an
    "_error" key describing the problem (we never raise from here so the rest
    of the pipeline can continue without metadata).
    """
    file_path = Path(file_path)
    exe = exiftool_path or "exiftool"

    if not file_path.is_file():
        return {"_error": f"File not found: {file_path}"}

    try:
        result = subprocess.run(
            [exe, "-json", "-charset", "filename=UTF8", str(file_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return {"_error": "ExifTool executable could not be run."}
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        return {"_error": f"ExifTool failed: {exc}"}

    if not result.stdout.strip():
        return {"_error": f"ExifTool returned no output. stderr: {result.stderr.strip()}"}

    try:
        # exiftool -json returns a LIST with one object per file.
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"_error": f"Could not parse ExifTool JSON: {exc}"}

    if isinstance(parsed, list) and parsed:
        return parsed[0]
    if isinstance(parsed, dict):
        return parsed
    return {"_error": "Unexpected ExifTool output format."}


# ---------------------------------------------------------------------------
# Flag analysis
# ---------------------------------------------------------------------------

# Metadata fields that commonly hold "which software made this" information.
_SOFTWARE_FIELDS = [
    "Software",
    "Creator",
    "CreatorTool",
    "Producer",
    "Application",
    "ProcessingSoftware",
    "HistorySoftwareAgent",
    "XMPToolkit",
]

# Date fields we compare for create/modify mismatches.
_CREATE_DATE_FIELDS = ["CreateDate", "DateTimeOriginal", "CreationDate"]
_MODIFY_DATE_FIELDS = ["ModifyDate", "FileModifyDate", "MetadataDate"]


def _collect_software_text(metadata: dict) -> str:
    """Join all the software-ish fields into one lowercase string for searching."""
    parts = []
    for field in _SOFTWARE_FIELDS:
        value = metadata.get(field)
        if value:
            parts.append(str(value))
    return " ".join(parts).lower()


def _first_present(metadata: dict, fields: list[str]) -> Optional[str]:
    """Return the first non-empty value among `fields`, else None."""
    for field in fields:
        value = metadata.get(field)
        if value:
            return str(value)
    return None


def analyze_metadata_flags(metadata: dict) -> dict:
    """
    Inspect metadata and return warning flags.

    Returns
    -------
    {
        "flags": [ list of short flag codes that fired ],
        "details": { flag_code: human-readable explanation },
        "software_seen": str,         # the software text we searched
        "metadata_available": bool,   # False if ExifTool failed
    }

    The flag codes are stable strings so the risk service can score them and
    the frontend can display them consistently.
    """
    flags: list[str] = []
    details: dict[str, str] = {}

    # If metadata extraction failed, report that as its own situation.
    if metadata.get("_error"):
        return {
            "flags": ["metadata_unavailable"],
            "details": {"metadata_unavailable": metadata["_error"]},
            "software_seen": "",
            "metadata_available": False,
        }

    software_text = _collect_software_text(metadata)

    # --- Known image/PDF editors -----------------------------------------
    editor_signatures = {
        "photoshop_detected": ["photoshop", "adobe photoshop"],
        "canva_detected": ["canva"],
        "gimp_detected": ["gimp"],
        "illustrator_coreldraw_detected": ["illustrator", "coreldraw", "corel draw"],
        "pdf_editor_detected": [
            "acrobat", "nitro", "foxit", "pdfelement", "pdf-xchange",
            "smallpdf", "ilovepdf", "sejda", "pdfescape",
        ],
    }
    for flag_code, signatures in editor_signatures.items():
        for sig in signatures:
            if sig in software_text:
                flags.append(flag_code)
                details[flag_code] = f"Software metadata mentions '{sig}'."
                break  # one hit per flag is enough

    # --- Date checks -----------------------------------------------------
    create_date = _first_present(metadata, _CREATE_DATE_FIELDS)
    modify_date = _first_present(metadata, _MODIFY_DATE_FIELDS)

    if not create_date and not modify_date:
        flags.append("missing_date_metadata")
        details["missing_date_metadata"] = "No create or modify date present in metadata."
    elif create_date and modify_date:
        # Compare just the timestamp text. We deliberately keep this simple:
        # a difference in the date string is treated as a 'mismatch' signal.
        # (ExifTool dates look like '2024:03:15 10:22:31'.)
        if create_date.strip() != modify_date.strip():
            flags.append("create_modify_mismatch")
            details["create_modify_mismatch"] = (
                f"CreateDate ('{create_date}') differs from ModifyDate ('{modify_date}')."
            )

    # --- Suspicious producer / creator -----------------------------------
    # A generic, blank, or web-tool producer on something claiming to be an
    # official document is a weak signal. We flag clearly online-editor-style
    # producers and obviously empty ones.
    producer = (metadata.get("Producer") or "").strip()
    creator = (metadata.get("Creator") or "").strip()
    suspicious_producer_terms = ["canva", "wkhtmltopdf", "skia/pdf", "online", "wps "]
    if producer:
        low = producer.lower()
        for term in suspicious_producer_terms:
            if term in low:
                flags.append("suspicious_producer_creator")
                details["suspicious_producer_creator"] = (
                    f"PDF Producer/Creator looks unusual for an official document: "
                    f"Producer='{producer}', Creator='{creator}'."
                )
                break

    # De-duplicate while preserving order (a flag could be added twice).
    unique_flags = list(dict.fromkeys(flags))

    return {
        "flags": unique_flags,
        "details": details,
        "software_seen": software_text,
        "metadata_available": True,
    }
