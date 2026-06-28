"""
document_loader_service.py
==========================

Loads the local policy documents (markdown files in docs/) and splits them into
small, self-contained CHUNKS for retrieval.

No network, no database — just reading local `.md` files. Each chunk records
which document and heading it came from, so the Policy Assistant can cite its
sources.
"""

from __future__ import annotations

import re
from pathlib import Path

# Target chunk size in characters. We pack whole paragraphs up to this size so
# chunks stay readable and self-contained (roughly 500–1000 chars as requested).
_TARGET_CHARS = 900
_MIN_CHARS = 350


def list_markdown_files(docs_dir: str | Path) -> list[Path]:
    """Return all .md files in docs_dir, sorted by name. Empty if none."""
    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        return []
    return sorted(docs_dir.glob("*.md"))


# Fenced code blocks (```...```) usually hold ASCII diagrams or shell commands.
# They make poor retrieval prose and leak garbled text into answers, so we strip
# them from the knowledge base. The surrounding prose still explains the same idea.
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)


def _read_text(path: Path) -> str:
    """Read a markdown file as UTF-8 (tolerating a BOM). Returns '' on failure."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return ""
    return _FENCED_CODE.sub(" ", text)


def _split_paragraphs(text: str):
    """Yield (heading, paragraph) pairs, tracking the most recent markdown heading."""
    heading = ""
    buffer: list[str] = []

    def flush():
        para = "\n".join(buffer).strip()
        buffer.clear()
        return para

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            # Emit any pending paragraph before switching heading.
            para = flush()
            if para:
                yield heading, para
            heading = stripped.lstrip("#").strip()
            continue
        if stripped == "":
            para = flush()
            if para:
                yield heading, para
        else:
            buffer.append(line)
    para = flush()
    if para:
        yield heading, para


def split_into_chunks(text: str, document: str) -> list[dict]:
    """
    Split one document's text into chunks of roughly _TARGET_CHARS characters by
    packing whole paragraphs together (never splitting mid-paragraph). Each chunk
    keeps its section heading for context.

    Returns a list of {document, chunk_id, heading, text}.
    """
    chunks: list[dict] = []
    current_heading = ""
    current_parts: list[str] = []
    current_len = 0

    def emit():
        nonlocal current_parts, current_len
        if not current_parts:
            return
        body = "\n\n".join(current_parts).strip()
        if body:
            chunk_id = f"{document}#{len(chunks)}"
            text_with_context = (f"[{current_heading}] {body}" if current_heading else body)
            chunks.append(
                {
                    "document": document,
                    "chunk_id": chunk_id,
                    "heading": current_heading,
                    "text": text_with_context,
                }
            )
        current_parts = []
        current_len = 0

    for heading, paragraph in _split_paragraphs(text):
        # When the heading changes, start a fresh chunk so context stays clean.
        if heading != current_heading and current_parts:
            emit()
        current_heading = heading

        para_len = len(paragraph)
        if current_len + para_len > _TARGET_CHARS and current_len >= _MIN_CHARS:
            emit()
        current_parts.append(paragraph)
        current_len += para_len

    emit()
    return chunks


def load_documents(docs_dir: str | Path) -> list[dict]:
    """
    Load and chunk every markdown file in docs_dir.

    Returns a flat list of chunk dicts: {document, chunk_id, heading, text}.
    """
    all_chunks: list[dict] = []
    for path in list_markdown_files(docs_dir):
        text = _read_text(path)
        if not text.strip():
            continue
        all_chunks.extend(split_into_chunks(text, path.name))
    return all_chunks
