"""
hashing.py
==========

Small helpers to compute SHA-256 hashes.

Why we hash uploaded files
--------------------------
A SHA-256 hash is a short "fingerprint" of the exact bytes of a file. We store
it with each case so we can:
    * detect if the SAME file was uploaded twice,
    * prove a stored file has not changed since upload,
    * reference a file without exposing its contents.

It is NOT a tamper-detection tool by itself (any edit produces a completely
different, equally-valid hash) — it just identifies the exact bytes we received.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of the given bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Return the SHA-256 hex digest of a file, read in chunks so even large
    files do not need to be loaded fully into memory.
    """
    file_path = Path(file_path)
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
