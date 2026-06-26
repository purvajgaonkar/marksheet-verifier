"""
pdf_service.py
==============

PDF handling for the marksheet verifier.

Many students upload their marksheet as a PDF (often a scan or an export from
a results portal). Our image-based pipeline (OpenCV + Tesseract) works on
pictures, so before we can analyze a PDF we must turn its FIRST PAGE into a
PNG image.

We use PyMuPDF (imported as `fitz`) because it is:
    * pure-pip installable (no system poppler needed, unlike pdf2image)
    * fast and reliable on Windows

This module does ONE job: render the first page of a PDF to a PNG file.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def is_pdf(file_path: str | Path) -> bool:
    """Return True if the path has a .pdf extension (case-insensitive)."""
    return Path(file_path).suffix.lower() == ".pdf"


def render_first_page_to_png(
    pdf_path: str | Path,
    output_path: str | Path,
    zoom: float = 2.0,
) -> Path:
    """
    Render the first page of `pdf_path` to a PNG saved at `output_path`.

    Parameters
    ----------
    pdf_path : path to the input PDF.
    output_path : where to write the rendered PNG.
    zoom : how much to scale up the page before rendering. A zoom of 2.0 means
           roughly 144 DPI (PDF default is 72 DPI x 2). Higher zoom = sharper
           image = better OCR, at the cost of a bigger file. 2.0-3.0 is a good
           range for marksheets.

    Returns
    -------
    Path to the written PNG file.

    Raises
    ------
    FileNotFoundError : if the PDF does not exist.
    ValueError : if the PDF has zero pages.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Make sure the output folder exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # `with` makes sure the document is closed even if something goes wrong.
    with fitz.open(pdf_path) as doc:
        if doc.page_count == 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")

        first_page = doc.load_page(0)  # page indices are 0-based

        # A "matrix" controls scaling. fitz.Matrix(zoom, zoom) scales both axes.
        matrix = fitz.Matrix(zoom, zoom)

        # Render the page to a pixmap (an in-memory image).
        pixmap = first_page.get_pixmap(matrix=matrix)

        # Save it to disk as PNG.
        pixmap.save(str(output_path))

    return output_path


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """
    Return the number of pages in a PDF. Useful for the report
    (a 1-page marksheet that suddenly has 5 pages may be worth a human glance).
    Returns 0 if the file cannot be opened.
    """
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except Exception:
        return 0
