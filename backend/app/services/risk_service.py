"""
risk_service.py
===============

Turns the evidence (metadata flags, OCR confidence, detected fields) into a
single demo RISK SCORE between 0.0 and 1.0, plus a human-readable LABEL.

IMPORTANT, please read
----------------------
This is an MVP scoring heuristic, NOT a fraud detector. The score is a weighted
sum of weak signals. It exists to PRIORITISE which uploads a human reviewer
should look at first. It must never be used to automatically reject a student.

Allowed status labels (exactly these six):
    verified           - no tampering signals detected (lowest risk band)
    low                - very minor signals, almost certainly fine
    medium             - some signals, worth a glance
    needs_review       - enough signals that a human SHOULD review it
    high               - many strong signals, prioritise human review
    unable_to_verify   - we could not analyse the file properly (e.g. OCR
                         produced nothing, or a required tool was missing)

Note that "verified" here means "our automated checks found no red flags",
NOT "officially verified against the board". Real verification needs the
board / DigiLocker / NAD, which is out of scope for this MVP.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# How much each signal adds to the risk score. Tunable, and intentionally
# transparent so the report can explain exactly why a score came out the way
# it did. Keep individual weights small so no single weak signal dominates.
# ---------------------------------------------------------------------------

_METADATA_FLAG_WEIGHTS = {
    "photoshop_detected": 0.25,
    "canva_detected": 0.25,
    "gimp_detected": 0.20,
    "illustrator_coreldraw_detected": 0.20,
    "pdf_editor_detected": 0.10,
    "create_modify_mismatch": 0.10,
    "missing_date_metadata": 0.08,
    "suspicious_producer_creator": 0.15,
}

# OCR confidence thresholds (0-100). Lower confidence => more risk.
_OCR_LOW_CONFIDENCE = 60.0       # below this, add a penalty
_OCR_VERY_LOW_CONFIDENCE = 40.0  # below this, add a bigger penalty

# Penalties for missing detected fields.
_MISSING_ROLL_PENALTY = 0.10
_MISSING_TOTAL_PENALTY = 0.08
_UNKNOWN_BOARD_PENALTY = 0.10
_OCR_LOW_PENALTY = 0.15
_OCR_VERY_LOW_PENALTY = 0.30

# Maximum the image forensics can ever add to the risk score. Forensics are
# WEAK evidence, so they are capped well below the OCR/metadata contributions
# and must never dominate the final score.
_FORENSICS_MAX_CONTRIBUTION = 0.20


def forensics_contribution(anomaly_score: float | None) -> float:
    """
    Map a 0..1 forensics anomaly score to a small, capped risk contribution.

    The bands are deliberately conservative and top out at 0.20 so that pixel
    signals can nudge — but never drive — the overall risk.
    """
    if anomaly_score is None:
        return 0.0
    if anomaly_score > 0.75:
        return _FORENSICS_MAX_CONTRIBUTION  # 0.20
    if anomaly_score > 0.50:
        return 0.12
    if anomaly_score > 0.30:
        return 0.06
    return 0.0


def _label_for_score(score: float) -> str:
    """
    Map a numeric score (0-1) to one of the standard risk labels.
    Thresholds are documented here and in the README so they are easy to tune.
    """
    if score < 0.15:
        return "verified"
    if score < 0.35:
        return "low"
    if score < 0.55:
        return "medium"
    if score < 0.75:
        return "needs_review"
    return "high"


def compute_risk(
    metadata_flags: dict,
    ocr_result: dict,
    fields: dict,
    forensics: dict | None = None,
) -> dict:
    """
    Combine all evidence into a risk score and label.

    Parameters
    ----------
    metadata_flags : output of metadata_service.analyze_metadata_flags()
    ocr_result     : output of ocr_service.extract_text_with_confidence()
    fields         : output of ocr_service.detect_fields()
    forensics      : output of forensics_service.run_forensics() (optional).
                     Only used when forensics["available"] is True, and capped
                     at +0.20 so it never dominates the score.

    Returns
    -------
    {
        "score": float,                 # 0.0 - 1.0, rounded to 3 decimals
        "label": str,                   # one of the six allowed labels
        "contributing_factors": [str],  # plain-English reasons, for the report
    }
    """
    score = 0.0
    factors: list[str] = []

    # ---- Special case: can we even analyse this file? -------------------
    text = (ocr_result or {}).get("text", "") or ""
    ocr_confidence = float((ocr_result or {}).get("average_confidence", 0.0))
    word_count = int((ocr_result or {}).get("word_count", 0))

    # If OCR found essentially no usable text, we cannot judge the document.
    if word_count == 0 or len(text.strip()) < 10:
        return {
            "score": 1.0,
            "label": "unable_to_verify",
            "contributing_factors": [
                "OCR produced little or no readable text, so the document "
                "could not be analysed automatically."
            ],
        }

    # ---- Metadata flag contributions ------------------------------------
    metadata_available = metadata_flags.get("metadata_available", True)
    if not metadata_available:
        # Missing metadata is a mild signal, not a failure of the whole run.
        score += 0.05
        factors.append("File metadata could not be read (mild signal).")

    for flag in metadata_flags.get("flags", []):
        weight = _METADATA_FLAG_WEIGHTS.get(flag)
        if weight:
            score += weight
            factors.append(f"Metadata flag '{flag}' added {weight:.2f} to the score.")

    # ---- OCR confidence contribution ------------------------------------
    if ocr_confidence < _OCR_VERY_LOW_CONFIDENCE:
        score += _OCR_VERY_LOW_PENALTY
        factors.append(
            f"Very low OCR confidence ({ocr_confidence:.1f}) added "
            f"{_OCR_VERY_LOW_PENALTY:.2f}."
        )
    elif ocr_confidence < _OCR_LOW_CONFIDENCE:
        score += _OCR_LOW_PENALTY
        factors.append(
            f"Low OCR confidence ({ocr_confidence:.1f}) added {_OCR_LOW_PENALTY:.2f}."
        )

    # ---- Missing-field contributions ------------------------------------
    if not fields.get("roll_number"):
        score += _MISSING_ROLL_PENALTY
        factors.append(
            f"No roll/seat number detected (added {_MISSING_ROLL_PENALTY:.2f})."
        )
    if not fields.get("total_marks"):
        score += _MISSING_TOTAL_PENALTY
        factors.append(
            f"No total marks detected (added {_MISSING_TOTAL_PENALTY:.2f})."
        )
    if fields.get("board", "unknown") == "unknown":
        score += _UNKNOWN_BOARD_PENALTY
        factors.append(
            f"Examination board could not be identified (added "
            f"{_UNKNOWN_BOARD_PENALTY:.2f})."
        )

    # ---- Image-forensics contribution (weak signal, capped at +0.20) ----
    if forensics and forensics.get("available"):
        anomaly = forensics.get("anomaly_score", 0.0)
        contrib = forensics_contribution(anomaly)
        if contrib > 0:
            score += contrib
            factors.append(
                f"Image-forensics anomaly score {anomaly} added {contrib:.2f} "
                f"(weak pixel signal, capped)."
            )

    # ---- Clamp to [0, 1] and label --------------------------------------
    score = max(0.0, min(1.0, score))
    label = _label_for_score(score)

    if not factors:
        factors.append("No tampering signals detected by the automated checks.")

    return {
        "score": round(score, 3),
        "label": label,
        "contributing_factors": factors,
    }
