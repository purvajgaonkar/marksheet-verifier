"""
file_utils.py
=============

Upload validation + safe filename helpers (Phase 10).

These centralise the security checks for every upload route so the same rules
apply to POST /upload and POST /student/submit:

  * sanitize_filename(name)                 - strip directories / unsafe chars
  * validate_upload_file(filename, data, …) - extension, size, non-empty, content
  * generate_safe_case_file_path(...)       - build an in-uploads path, no traversal

Defence in depth: we never trust the user's filename for a path, we cap the size,
and we sniff magic bytes so a renamed .exe/.zip/.html cannot pose as a PDF/image.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from app import config


class UploadValidationError(Exception):
    """A client-side problem with an uploaded file (bad type/size/empty/content)."""


# Magic-byte signatures for the file types we accept. Validating these (not just
# the extension) blocks a malicious file renamed to a permitted extension.
_MAGIC = {
    ".pdf": [b"%PDF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
}


def sanitize_filename(filename: str) -> str:
    """
    Turn a user-supplied filename into something safe to store.

    Strips any directory components (defeats path traversal like
    "..\\..\\windows\\system32\\evil.exe"), keeps only letters/numbers/dot/dash/
    underscore, and falls back to "upload" if nothing usable remains.
    """
    name = Path(filename or "").name  # final component only, never a folder
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.strip("._") or "upload"
    return name


def _looks_like_allowed_content(extension: str, file_bytes: bytes) -> bool:
    """True if the leading bytes match a known signature for this extension."""
    signatures = _MAGIC.get(extension)
    if not signatures:
        # No signature known for this (configured-but-unusual) extension: don't
        # block on content — the extension allow-list already gated it.
        return True
    head = file_bytes[:16]
    if extension == ".pdf":
        # Tolerate a few leading bytes (some tools prepend whitespace/BOM).
        return b"%PDF" in file_bytes[:1024]
    return any(head.startswith(sig) for sig in signatures)


def validate_upload_file(
    filename: str,
    file_bytes: bytes,
    *,
    content_type: Optional[str] = None,
) -> str:
    """
    Validate an upload. Returns the normalised lowercase extension (e.g. ".pdf")
    on success, or raises UploadValidationError with a safe, user-facing message.

    Checks: non-empty filename, allowed extension, non-empty content, size within
    MAX_UPLOAD_SIZE_MB, and magic-byte content sniffing.
    """
    if not filename:
        raise UploadValidationError("No filename was provided.")

    extension = Path(filename).suffix.lower()
    allowed = config.ALLOWED_UPLOAD_EXTENSIONS
    if extension not in allowed:
        raise UploadValidationError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(allowed))}."
        )

    if not file_bytes:
        raise UploadValidationError("The uploaded file is empty.")

    if len(file_bytes) > config.MAX_UPLOAD_SIZE_BYTES:
        raise UploadValidationError(
            f"File is too large. The maximum allowed size is "
            f"{config.MAX_UPLOAD_SIZE_MB} MB."
        )

    # If the browser sent an obviously dangerous content type, reject early with
    # a friendly message (the magic-byte check below is the real gate).
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        _BLOCKED_CT = {
            "application/zip",
            "application/x-zip-compressed",
            "application/x-msdownload",
            "application/x-dosexec",
            "text/html",
            "application/javascript",
            "text/javascript",
        }
        if ct in _BLOCKED_CT:
            raise UploadValidationError("This file type is not allowed.")

    if not _looks_like_allowed_content(extension, file_bytes):
        raise UploadValidationError(
            "The file's contents do not match its extension. Please upload a "
            "genuine PDF, PNG, or JPG file."
        )

    return extension


def generate_safe_case_file_path(
    case_id: str,
    original_filename: str,
    uploads_dir: str | Path,
) -> dict:
    """
    Build a safe absolute path inside uploads_dir for this case's file.

    The stored name is "<case_id>_<sanitized original>", so the user's filename
    is never used as a directory and two identical names can't collide. Returns
    {"stored_path": Path, "stored_filename": str, "safe_original": str}.
    """
    uploads_dir = Path(uploads_dir)
    safe_original = sanitize_filename(original_filename)
    stored_filename = f"{case_id}_{safe_original}"
    stored_path = (uploads_dir / stored_filename).resolve()

    # Final guard: the resolved path MUST stay within uploads_dir.
    uploads_root = uploads_dir.resolve()
    if uploads_root not in stored_path.parents and stored_path.parent != uploads_root:
        raise UploadValidationError("Invalid upload path.")

    return {
        "stored_path": stored_path,
        "stored_filename": stored_filename,
        "safe_original": safe_original,
    }
