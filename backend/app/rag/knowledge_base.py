"""
knowledge_base.py
=================

An in-memory knowledge base for the local RAG assistant. It loads and chunks the
docs/ markdown files, builds a retriever (TF-IDF or keyword fallback), and
answers `search()` queries with the most relevant chunks.

A single shared instance is used across requests (get_knowledge_base()). It
builds lazily on first use and can be rebuilt with reindex() after the docs
change. A lock keeps concurrent FastAPI requests from racing on a rebuild.
"""

from __future__ import annotations

import threading
from pathlib import Path

from app import config
from app.services import document_loader_service, retrieval_service

_PREVIEW_CHARS = 220


class KnowledgeBase:
    def __init__(self, docs_dir: str | Path):
        self.docs_dir = Path(docs_dir)
        self._chunks: list[dict] = []
        self._retriever = None
        self._mode = "local_tfidf"
        self._built = False
        self._lock = threading.Lock()

    # -- building -----------------------------------------------------------
    def build(self) -> None:
        """Load docs, chunk them, and build the retriever (thread-safe)."""
        with self._lock:
            chunks = document_loader_service.load_documents(self.docs_dir)
            texts = [c["text"] for c in chunks]
            retriever = retrieval_service.build_retriever(texts)
            self._chunks = chunks
            self._retriever = retriever
            self._mode = getattr(retriever, "mode", "local_tfidf")
            self._built = True

    def ensure_built(self) -> None:
        if not self._built:
            self.build()

    def reindex(self) -> dict:
        """Force a rebuild from disk and return the new source summary."""
        self.build()
        return self.sources()

    # -- queries ------------------------------------------------------------
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Return up to top_k relevant chunks, each as:
            {document, chunk_id, heading, text, preview, score}
        """
        self.ensure_built()
        if not self._chunks or self._retriever is None:
            return []
        results = []
        for index, score in self._retriever.query(query, top_k):
            chunk = self._chunks[index]
            preview = chunk["text"].strip().replace("\n", " ")
            if len(preview) > _PREVIEW_CHARS:
                preview = preview[:_PREVIEW_CHARS].rstrip() + "…"
            results.append(
                {
                    "document": chunk["document"],
                    "chunk_id": chunk["chunk_id"],
                    "heading": chunk.get("heading", ""),
                    "text": chunk["text"],
                    "preview": preview,
                    "score": round(float(score), 4),
                }
            )
        return results

    def sources(self) -> dict:
        """Summarise the indexed documents (for GET /rag/sources)."""
        self.ensure_built()
        documents = sorted({c["document"] for c in self._chunks})
        return {
            "documents": documents,
            "chunk_count": len(self._chunks),
            "mode": self._mode,
        }


# ---------------------------------------------------------------------------
# Shared singleton
# ---------------------------------------------------------------------------
_kb: KnowledgeBase | None = None
_kb_lock = threading.Lock()


def get_knowledge_base() -> KnowledgeBase:
    """Return the shared KnowledgeBase, creating it on first use."""
    global _kb
    if _kb is None:
        with _kb_lock:
            if _kb is None:
                _kb = KnowledgeBase(config.DOCS_DIR)
    return _kb
