"""
command_checks.py
=================

Helpers to LOCATE and VERIFY the two external command-line tools this project
depends on:

    * Tesseract OCR  -> reads text out of images
    * ExifTool       -> reads file metadata (who/what created the file)

Why this file exists
--------------------
On Windows these tools are very often *installed* but NOT on the system PATH,
or the PATH was updated AFTER the terminal was opened (so the current shell
does not see them yet). That makes `tesseract --version` fail even though the
program is sitting right there on disk.

To stay beginner-friendly and avoid mysterious crashes, every lookup here:

    1. First checks the system PATH (via shutil.which).
    2. If not found, falls back to a list of common Windows install locations.
    3. Returns the resolved absolute path, or None if it truly cannot be found.

Nothing in this file raises an exception on import. Callers look at the
returned dictionary and decide what to do (warn the user, skip a step, etc.).
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Known fallback locations (checked only if the tool is not already on PATH).
# Add more paths here if your machine installs the tools somewhere unusual.
# ---------------------------------------------------------------------------

_TESSERACT_FALLBACKS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
]

_EXIFTOOL_FALLBACKS = [
    r"C:\Tools\ExifTool\exiftool.exe",
    r"C:\Program Files\ExifTool\exiftool.exe",
    r"C:\Program Files (x86)\ExifTool\exiftool.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\ExifTool\exiftool.exe"),
]

# ExifTool is frequently downloaded as a zip that extracts to a folder like
# "exiftool-13.59_64\exiftool.exe" in Downloads. We glob for that pattern too.
_EXIFTOOL_GLOB_PATTERNS = [
    os.path.expandvars(r"%USERPROFILE%\Downloads\exiftool*\exiftool*.exe"),
]


def _first_existing(paths) -> Optional[str]:
    """Return the first path in `paths` that exists on disk, else None."""
    for p in paths:
        if p and Path(p).is_file():
            return str(Path(p).resolve())
    return None


def _resolve_from_globs(patterns) -> Optional[str]:
    """Return the first file matching any of the given glob patterns, else None."""
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return str(Path(matches[0]).resolve())
    return None


def find_tesseract() -> Optional[str]:
    """
    Locate the tesseract executable.

    Returns the absolute path as a string, or None if it cannot be found.
    """
    # 1) On PATH?  (works on Windows, macOS and Linux)
    on_path = shutil.which("tesseract")
    if on_path:
        return str(Path(on_path).resolve())

    # 2) Common Windows install locations.
    return _first_existing(_TESSERACT_FALLBACKS)


def find_exiftool() -> Optional[str]:
    """
    Locate the exiftool executable.

    Returns the absolute path as a string, or None if it cannot be found.
    """
    # 1) On PATH?  ExifTool is sometimes named "exiftool" or "exiftool.exe".
    for name in ("exiftool", "exiftool.exe"):
        on_path = shutil.which(name)
        if on_path:
            return str(Path(on_path).resolve())

    # 2) Common fixed install locations.
    fixed = _first_existing(_EXIFTOOL_FALLBACKS)
    if fixed:
        return fixed

    # 3) The "extracted zip in Downloads" pattern.
    return _resolve_from_globs(_EXIFTOOL_GLOB_PATTERNS)


def _run_version(tool_path: str, version_args) -> Optional[str]:
    """
    Run `tool_path <version_args>` and return the first line of output.

    Returns None if the command could not be run. Never raises.
    """
    try:
        result = subprocess.run(
            [tool_path, *version_args],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return None

    # Tesseract prints its version banner to stdout; some tools use stderr.
    output = (result.stdout or "").strip() or (result.stderr or "").strip()
    if not output:
        return None
    return output.splitlines()[0].strip()


def check_tesseract() -> dict:
    """
    Return a status dictionary for Tesseract:
        {
            "name": "tesseract",
            "available": bool,
            "path": str | None,
            "version": str | None,
            "error": str | None,
        }
    """
    path = find_tesseract()
    if not path:
        return {
            "name": "tesseract",
            "available": False,
            "path": None,
            "version": None,
            "error": "Tesseract executable not found on PATH or in common locations.",
        }

    version = _run_version(path, ["--version"])
    return {
        "name": "tesseract",
        "available": version is not None,
        "path": path,
        "version": version,
        "error": None if version else "Found tesseract but could not run it.",
    }


def check_exiftool() -> dict:
    """
    Return a status dictionary for ExifTool (same shape as check_tesseract()).
    """
    path = find_exiftool()
    if not path:
        return {
            "name": "exiftool",
            "available": False,
            "path": None,
            "version": None,
            "error": "ExifTool executable not found on PATH or in common locations.",
        }

    version = _run_version(path, ["-ver"])
    return {
        "name": "exiftool",
        "available": version is not None,
        "path": path,
        "version": version,
        "error": None if version else "Found exiftool but could not run it.",
    }


def check_all_tools() -> dict:
    """
    Convenience wrapper that checks every external tool at once.

    Returns:
        {
            "tesseract": {...status dict...},
            "exiftool":  {...status dict...},
        }
    """
    return {
        "tesseract": check_tesseract(),
        "exiftool": check_exiftool(),
    }
