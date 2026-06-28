"""
rag_routes.py
=============

Endpoints for the local RAG Policy Assistant (Phase 6). Everything is local —
no external AI/LLM API, no API key.

    POST /rag/ask      -> answer a reviewer question (optionally case-aware)
    GET  /rag/sources  -> list indexed documents + chunk count + retrieval mode
    POST /rag/reindex  -> rebuild the in-memory index from docs/
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import RagAskRequest
from app.services import rag_service

router = APIRouter(tags=["rag"])


@router.post("/rag/ask")
def ask(request: RagAskRequest) -> dict:
    """Answer a reviewer question using local policy documents."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="A 'question' is required.")
    return rag_service.answer_question(request.question, request.case_id)


@router.get("/rag/sources")
def sources() -> dict:
    """Return the indexed documents, chunk count, and retrieval mode."""
    return rag_service.get_sources()


@router.post("/rag/reindex")
def reindex() -> dict:
    """Rebuild the in-memory index from docs/ (use after editing the docs)."""
    summary = rag_service.reindex()
    return {"reindexed": True, **summary}
