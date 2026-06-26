"""
analysis_service.py
===================

The SHARED analyzer pipeline used by BOTH:
    * the command-line tool  (backend/analyze.py)        -> Phase 1
    * the FastAPI upload route (app/routes/upload_routes) -> Phase 2

This module contains the exact same logic that was in Phase 1's analyze.py,
moved here so it is not duplicated. analyze.py now calls `analyze_file()` and
so does the web upload route. Behaviour for the CLI is unchanged.

`analyze_file()` does steps 1-8 of the pipeline and RETURNS the report as a
Python dict. It deliberately does NOT save the report to disk — the caller
decides where to save it (the CLI saves it under the file's name; the API saves
it under the case_id).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services import (
    image_preprocess_service,
    metadata_service,
    ocr_service,
    pdf_service,
    report_service,
    risk_service,
)
from app.utils import command_checks

# File types we can analyze.
SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class AnalyzerError(Exception):
    """
    Raised for problems the caller is expected to handle gracefully, e.g.
    an unsupported file type or a missing OCR tool. The CLI turns this into a
    friendly message; the API turns it into an HTTP error response.
    """


def _log(verbose: bool, message: str) -> None:
    """Print progress only when running interactively (the CLI)."""
    if verbose:
        print(message)


def analyze_file(
    input_path: str | Path,
    *,
    forensic_dir: str | Path,
    base_name: Optional[str] = None,
    display_name: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """
    Run the full analysis pipeline on a single file and return a report dict.

    Parameters
    ----------
    input_path  : the file on disk to analyze (PDF / JPG / JPEG / PNG).
    forensic_dir: folder where intermediate/debug images are written.
    base_name   : prefix for the debug images. Defaults to the file's stem.
                  (The API passes the case_id so files never collide.)
    display_name: the name to record in the report as the original file name.
                  Defaults to the input file's name. (The API passes the
                  student's original upload name even though the stored file is
                  renamed with the case_id.)
    verbose     : when True, print step-by-step progress (used by the CLI).

    Returns
    -------
    dict : the full report (see report_service.build_report).

    Raises
    ------
    AnalyzerError : for missing files, unsupported types, or a missing
                    Tesseract installation.
    """
    input_path = Path(input_path)
    forensic_dir = Path(forensic_dir)

    # --- 1. Validate the input file --------------------------------------
    if not input_path.exists():
        raise AnalyzerError(f"Input file does not exist: {input_path}")

    extension = input_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise AnalyzerError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    base_name = base_name or input_path.stem
    display_name = display_name or input_path.name
    _log(verbose, f"[1/8] Analyzing: {display_name}")

    # --- 2. Check external tools -----------------------------------------
    tools = command_checks.check_all_tools()
    tess = tools["tesseract"]
    exif = tools["exiftool"]

    _log(verbose, f"[2/8] Tesseract : "
                  f"{'OK ' + str(tess['version']) if tess['available'] else 'NOT AVAILABLE'}")
    _log(verbose, f"      ExifTool  : "
                  f"{'OK ' + str(exif['version']) if exif['available'] else 'NOT AVAILABLE'}")

    # OCR is essential. Without Tesseract we cannot continue meaningfully.
    if not tess["available"]:
        raise AnalyzerError(
            "Tesseract OCR is required but was not found. "
            f"Detail: {tess.get('error')}. "
            "Install it from https://github.com/UB-Mannheim/tesseract/wiki and "
            "either add it to PATH or to a known location, then re-run."
        )

    # Point pytesseract at the resolved tesseract.exe.
    ocr_service.configure_tesseract(tess["path"])

    if not exif["available"]:
        _log(verbose, "      (ExifTool not available - metadata checks will be skipped.)")

    # --- 3. If PDF, render first page to PNG -----------------------------
    pdf_page_count = None
    if pdf_service.is_pdf(input_path):
        _log(verbose, "[3/8] Input is a PDF - rendering first page to PNG...")
        pdf_page_count = pdf_service.get_pdf_page_count(input_path)
        rendered_png = forensic_dir / f"{base_name}__pdf_page1.png"
        try:
            image_for_ocr = pdf_service.render_first_page_to_png(input_path, rendered_png)
        except Exception as exc:  # noqa: BLE001
            raise AnalyzerError(f"Failed to render PDF: {exc}") from exc
    else:
        _log(verbose, "[3/8] Input is an image - no PDF rendering needed.")
        image_for_ocr = input_path

    # --- 4. Preprocess image ---------------------------------------------
    _log(verbose, "[4/8] Preprocessing image (grayscale/resize/denoise/threshold)...")
    try:
        preprocess_info = image_preprocess_service.preprocess_for_ocr(
            image_for_ocr, forensic_dir, base_name
        )
    except Exception as exc:  # noqa: BLE001
        raise AnalyzerError(f"Image preprocessing failed: {exc}") from exc

    # --- 5. OCR + field detection ----------------------------------------
    _log(verbose, "[5/8] Running OCR...")
    ocr_result = ocr_service.extract_text_with_confidence(
        preprocess_info["preprocessed_image"]
    )
    fields = ocr_service.detect_fields(ocr_result["text"])
    _log(verbose, f"      OCR confidence: {ocr_result['average_confidence']} "
                  f"({ocr_result['word_count']} words)")

    # --- 6. Metadata + flags ---------------------------------------------
    _log(verbose, "[6/8] Reading file metadata...")
    raw_metadata = metadata_service.extract_metadata(input_path, exif.get("path"))
    metadata_flags = metadata_service.analyze_metadata_flags(raw_metadata)
    if verbose:
        if metadata_flags["flags"]:
            _log(verbose, f"      Metadata flags: {', '.join(metadata_flags['flags'])}")
        else:
            _log(verbose, "      Metadata flags: none")

    # --- 7. Risk score ---------------------------------------------------
    _log(verbose, "[7/8] Computing risk score...")
    risk = risk_service.compute_risk(metadata_flags, ocr_result, fields)

    # --- 8. Build the report (the caller saves it) -----------------------
    _log(verbose, "[8/8] Building report...")
    report = report_service.build_report(
        file_name=display_name,
        file_path=str(input_path.resolve()),
        file_type=extension.lstrip("."),
        analyzed_at=datetime.now().isoformat(timespec="seconds"),
        tools=tools,
        ocr_result=ocr_result,
        fields=fields,
        metadata_flags=metadata_flags,
        risk=risk,
        preprocess_info=preprocess_info,
        pdf_page_count=pdf_page_count,
        raw_metadata=raw_metadata,
    )
    return report
