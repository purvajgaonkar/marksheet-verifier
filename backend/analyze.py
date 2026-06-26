"""
analyze.py  -  Phase 1 command-line marksheet analyzer
======================================================

This is the entry point for the offline (no server, no frontend) analyzer.

As of Phase 2, the actual pipeline lives in
    app/services/analysis_service.py
so that the FastAPI server and this command-line tool run the EXACT SAME code.
This file is now a thin, friendly wrapper around that shared pipeline:

    1.  Read the input-file argument from the command line.
    2.  Call analysis_service.analyze_file(...) to do all the work.
    3.  Save the JSON report to reports/ and print a terminal summary.

Run it like this (from the project root, with the venv active):

    python backend/analyze.py uploads/dummy_marksheet.png
    python backend/analyze.py sample_data/dummy_marksheet.png
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the `app` package importable no matter where we are run from.
# analyze.py lives in   <project>/backend/analyze.py
# the package lives in  <project>/backend/app
# so we add <project>/backend to the import path.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import config  # noqa: E402  (import after sys.path tweak)
from app.services import report_service  # noqa: E402
from app.services.analysis_service import AnalyzerError, analyze_file  # noqa: E402


def _fail(message: str, exit_code: int = 1) -> None:
    """Print an error and exit. Keeps the main flow easy to read."""
    print(f"\n[ERROR] {message}\n")
    sys.exit(exit_code)


def _parse_args() -> Path:
    """Read the single input-file argument from the command line."""
    if len(sys.argv) != 2:
        print("Usage:")
        print("    python backend/analyze.py <path-to-marksheet>")
        print("Examples:")
        print("    python backend/analyze.py uploads/dummy_marksheet.png")
        print("    python backend/analyze.py sample_data/dummy_marksheet.png")
        sys.exit(2)
    return Path(sys.argv[1])


def main() -> None:
    input_path = _parse_args()

    # Friendly pre-check so a missing file gives clear guidance (not a stack trace).
    if not input_path.exists():
        _fail(
            f"Input file does not exist: {input_path}\n"
            f"Put a sample file in the uploads/ folder, or generate the demo "
            f"sample (see README), then try again."
        )

    config.ensure_directories()
    base_name = input_path.stem  # filename without extension

    # Run the shared pipeline (verbose=True prints the [1/8]..[8/8] progress).
    try:
        report = analyze_file(
            input_path,
            forensic_dir=config.FORENSIC_OUTPUTS_DIR,
            base_name=base_name,
            verbose=True,
        )
    except AnalyzerError as exc:
        _fail(str(exc))

    # Save the report and print a friendly summary.
    report_path = report_service.save_report(report, config.REPORTS_DIR, base_name)
    report_service.print_summary(report, report_path)


if __name__ == "__main__":
    main()
