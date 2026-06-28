"""
file_storage.py
===============

Two jobs, both using only the local filesystem (no real database in this MVP):

1. Save an uploaded file safely into uploads/.
2. Maintain a tiny JSON "database" of cases at reports/cases_index.json.

The cases index is just a JSON list. Each item is one case (one upload). This
is intentionally simple and human-readable for the MVP; PostgreSQL comes later.

Windows note: we always build paths with pathlib and strip any directory parts
from the user-supplied filename, so an upload can never write outside uploads/.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Saving uploaded files
# ---------------------------------------------------------------------------

def _safe_filename(filename: str) -> str:
    """
    Turn a user-supplied filename into something safe to write to disk.

    * Strips any directory components (prevents path traversal like
      "..\\..\\windows\\system32\\evil.exe").
    * Replaces unusual characters with underscores.
    * Falls back to "upload" if nothing usable remains.
    """
    # Keep only the final name part, never any folders.
    name = Path(filename).name
    # Allow letters, numbers, dot, dash, underscore. Replace the rest.
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.strip("._") or "upload"
    return name


def save_upload(
    file_bytes: bytes,
    original_filename: str,
    case_id: str,
    uploads_dir: str | Path,
) -> dict:
    """
    Save uploaded bytes into uploads/ using a collision-proof name.

    The stored name is "<case_id>_<safe original name>" so two students who both
    upload "marksheet.png" never overwrite each other.

    Returns
    -------
    {
        "stored_path": Path,        # absolute path on disk
        "stored_filename": str,     # just the file name we used
        "safe_original": str,       # cleaned original name
    }
    """
    uploads_dir = Path(uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_original = _safe_filename(original_filename)
    stored_filename = f"{case_id}_{safe_original}"
    stored_path = uploads_dir / stored_filename

    with open(stored_path, "wb") as fh:
        fh.write(file_bytes)

    return {
        "stored_path": stored_path,
        "stored_filename": stored_filename,
        "safe_original": safe_original,
    }


# ---------------------------------------------------------------------------
# The cases index (our local JSON "database")
# ---------------------------------------------------------------------------

def load_cases_index(cases_index_path: str | Path) -> list[dict]:
    """
    Read all cases from the index file. Returns an empty list if the file does
    not exist yet or is unreadable/corrupt (we never crash the API over this).
    """
    cases_index_path = Path(cases_index_path)
    if not cases_index_path.is_file():
        return []
    try:
        # utf-8-sig tolerates a BOM, which Windows editors (and PowerShell's
        # Set-Content -Encoding utf8) can prepend. Plain utf-8 would choke on it.
        with open(cases_index_path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return []
    # Be tolerant: only accept a list of dicts.
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def save_cases_index(cases_index_path: str | Path, cases: list[dict]) -> None:
    """Write the full list of cases back to the index file (indented JSON)."""
    cases_index_path = Path(cases_index_path)
    cases_index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cases_index_path, "w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=2, ensure_ascii=False)


def add_case(cases_index_path: str | Path, case_entry: dict) -> None:
    """Append one case to the index (load, append, save)."""
    cases = load_cases_index(cases_index_path)
    cases.append(case_entry)
    save_cases_index(cases_index_path, cases)


def get_case(cases_index_path: str | Path, case_id: str) -> Optional[dict]:
    """Return a single case entry by its case_id, or None if not found."""
    for case in load_cases_index(cases_index_path):
        if case.get("case_id") == case_id:
            return case
    return None
