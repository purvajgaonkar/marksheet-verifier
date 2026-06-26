"""
ocr_service.py
==============

Optical Character Recognition (OCR) using Tesseract via the `pytesseract`
Python wrapper, PLUS some simple rule-based field detection.

Responsibilities
----------------
1. Point pytesseract at the correct tesseract.exe (Windows PATH is unreliable).
2. Extract the full text from a preprocessed image.
3. Compute an AVERAGE OCR CONFIDENCE (how sure Tesseract was, 0-100).
4. Detect a few marksheet fields with plain regular expressions:
       - board (CBSE / ICSE / ISC / State Board / unknown)
       - roll / seat number
       - total marks
       - percentage
       - result keywords (pass / fail / etc.)

These detectors are intentionally simple and explainable. They are NOT meant
to be perfect — they feed the risk score as weak signals, and a human always
makes the final call.
"""

from __future__ import annotations

import re
from typing import Optional

import numpy as np
import pytesseract


# A tolerant "separator" between a field label and its value. OCR frequently
# turns a colon ':' into things like '=', '=:', '.', or '-', so we allow a
# short run of any of these (plus spaces) instead of a single fixed character.
_SEP = r"[\s:=.\-]{0,4}"


def configure_tesseract(tesseract_path: Optional[str]) -> None:
    """
    Tell pytesseract where tesseract.exe lives.

    Call this once (with the path from command_checks.find_tesseract())
    before running any OCR. If `tesseract_path` is None we leave pytesseract
    on its default, which assumes tesseract is on PATH.
    """
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def extract_text(image: np.ndarray) -> str:
    """Return the plain text Tesseract reads from the image."""
    return pytesseract.image_to_string(image)


def extract_text_with_confidence(image: np.ndarray) -> dict:
    """
    Run OCR and also compute an average confidence.

    pytesseract.image_to_data returns per-word data including a confidence
    value (0-100, or -1 for non-text blocks). We average the valid word
    confidences to get a single number that hints at overall OCR quality.

    Returns
    -------
    {
        "text": str,                # full recognised text
        "average_confidence": float,# 0-100, or 0.0 if no words found
        "word_count": int,          # number of confident words used
    }
    """
    # First, the readable text.
    text = pytesseract.image_to_string(image)

    # Then, the detailed per-word data for confidence.
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    confidences = []
    for conf, word in zip(data.get("conf", []), data.get("text", [])):
        # conf can be a string like "-1" or "95". Skip empty words and -1.
        try:
            conf_value = float(conf)
        except (TypeError, ValueError):
            continue
        if conf_value >= 0 and word and word.strip():
            confidences.append(conf_value)

    if confidences:
        average_confidence = sum(confidences) / len(confidences)
    else:
        average_confidence = 0.0

    return {
        "text": text,
        "average_confidence": round(average_confidence, 2),
        "word_count": len(confidences),
    }


# ---------------------------------------------------------------------------
# Field detection (simple, explainable regex rules)
# ---------------------------------------------------------------------------

def _detect_board(text_upper: str) -> str:
    """
    Guess the examination board from keywords.

    Order matters: we check the more specific 'ISC'/'ICSE' before generic
    'state board'. Returns one of:
        'CBSE', 'ICSE', 'ISC', 'State Board', 'unknown'
    """
    # Use word-ish boundaries so 'ISC' inside another word doesn't false-match.
    if re.search(r"\bCBSE\b", text_upper) or "CENTRAL BOARD OF SECONDARY" in text_upper:
        return "CBSE"
    if re.search(r"\bICSE\b", text_upper) or "INDIAN CERTIFICATE OF SECONDARY" in text_upper:
        return "ICSE"
    if re.search(r"\bISC\b", text_upper) or "INDIAN SCHOOL CERTIFICATE" in text_upper:
        return "ISC"
    if "STATE BOARD" in text_upper or "BOARD OF SECONDARY EDUCATION" in text_upper:
        return "State Board"
    return "unknown"


def _detect_roll_number(text: str) -> Optional[str]:
    """
    Find a roll number / seat number / registration number if present.

    We look for a label like 'Roll No', 'Seat No', 'Registration No' followed
    by an alphanumeric code. Returns the matched value, or None.
    """
    patterns = [
        rf"(?:roll\s*(?:no|number|n0)?{_SEP})([A-Z0-9\-/]{{4,}})",
        rf"(?:seat\s*(?:no|number)?{_SEP})([A-Z0-9\-/]{{4,}})",
        rf"(?:reg(?:istration)?\s*(?:no|number)?{_SEP})([A-Z0-9\-/]{{4,}})",
        rf"(?:enroll?ment\s*(?:no|number)?{_SEP})([A-Z0-9\-/]{{4,}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _detect_total_marks(text: str) -> Optional[str]:
    """
    Find a 'total marks' style value, e.g. 'Total: 456/500' or 'Total Marks 456'.
    Returns the matched value as text, or None.
    """
    patterns = [
        rf"total\s*(?:marks)?{_SEP}(\d{{2,4}}\s*/\s*\d{{2,4}})",  # 456/500
        rf"total\s*(?:marks)?{_SEP}(\d{{2,4}})",                  # 456
        rf"grand\s*total{_SEP}(\d{{2,4}}\s*/?\s*\d{{0,4}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _detect_percentage(text: str) -> Optional[str]:
    """
    Find a percentage value, e.g. '91.2%' or 'Percentage : 91.2'.
    Returns the matched value as text, or None.
    """
    patterns = [
        rf"percentage{_SEP}(\d{{1,3}}(?:\.\d{{1,2}})?)\s*%?",
        r"(\d{1,3}(?:\.\d{1,2})?)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Sanity check: a percentage should be 0-100.
            try:
                if 0 <= float(value) <= 100:
                    return value
            except ValueError:
                continue
    return None


def _detect_result_keywords(text_upper: str) -> list[str]:
    """Return any result-related keywords found (PASS, FAIL, etc.)."""
    keywords = ["PASS", "FAIL", "QUALIFIED", "PROMOTED", "COMPARTMENT", "DISTINCTION"]
    found = []
    for kw in keywords:
        if re.search(rf"\b{kw}\b", text_upper):
            found.append(kw)
    return found


def detect_fields(text: str) -> dict:
    """
    Run all the simple field detectors on the OCR text.

    Returns a dictionary describing what we found. Missing fields are None
    (or an empty list), which the risk score treats as a weak warning signal.
    """
    text_upper = text.upper()
    return {
        "board": _detect_board(text_upper),
        "roll_number": _detect_roll_number(text),
        "total_marks": _detect_total_marks(text),
        "percentage": _detect_percentage(text),
        "result_keywords": _detect_result_keywords(text_upper),
    }
