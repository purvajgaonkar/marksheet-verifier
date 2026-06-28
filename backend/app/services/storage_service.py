"""
storage_service.py
==================

A thin storage abstraction (Phase 10).

Right now this implements LOCAL filesystem storage only (it delegates to
file_storage), but it is the single seam through which uploaded files are saved.
When the project moves to a real deployment, swap the body of save_upload() for
an object-storage backend without touching the rest of the app.

Architecture / deployment notes
--------------------------------
  * The local `uploads/` directory is for DEVELOPMENT. On ephemeral hosting
    (Render free tier, etc.) the local disk is not persistent.
  * PRODUCTION should use object storage — Supabase Storage, AWS S3, or
    Cloudflare R2 — and store the returned object path / URL in the database
    (the `Case.file_path` column already holds a path string).
  * To add a cloud backend later: introduce a STORAGE_BACKEND env var, and in
    save_upload() branch on it (e.g. "local" vs "s3"/"supabase"), returning the
    same dict shape so callers don't change.

The returned dict shape is stable:
    {"stored_path": Path|str, "stored_filename": str, "safe_original": str}
"""

from __future__ import annotations

from pathlib import Path

from app import config
from app.services import file_storage

# Future: read STORAGE_BACKEND from the environment and dispatch here.
STORAGE_BACKEND = "local"


def save_upload(file_bytes: bytes, original_filename: str, case_id: str) -> dict:
    """
    Persist an uploaded file and return where it landed.

    Local backend (current): writes into config.UPLOADS_DIR as
    "<case_id>_<safe original>". The filename is sanitised and can never escape
    the uploads directory (see file_storage / file_utils).

    # TODO(cloud): when STORAGE_BACKEND != "local", upload the bytes to object
    # storage (Supabase/S3/R2) and return the object key/URL as "stored_path".
    """
    return file_storage.save_upload(
        file_bytes=file_bytes,
        original_filename=original_filename,
        case_id=case_id,
        uploads_dir=config.UPLOADS_DIR,
    )


def local_uploads_dir() -> Path:
    """The directory used by the local backend (handy for tests/diagnostics)."""
    return Path(config.UPLOADS_DIR)
