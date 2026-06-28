"""
claude_service.py
=================

Optional Claude API answer generation for the Policy Assistant (Phase 7).

This is the ONLY place that talks to the Anthropic API. It is used purely to
phrase a better, source-grounded answer on top of the SAME retrieved policy
context the local fallback uses. It never makes decisions.

Key guarantees:
    * The API key is read from config (which loads it from the environment /
      backend/.env). It is never hardcoded and never returned to callers.
    * The Anthropic client is created lazily and only if a key exists.
    * generate_claude_rag_answer() NEVER raises — on any problem it returns a
      dict with available=False so the caller can fall back to local answers.
    * Claude output is treated as an EXPLANATION only. It cannot change the risk
      score, status, reports, or any reviewer decision (the caller never lets it).
"""

from __future__ import annotations

import logging
from typing import Optional

from app import config
from app.prompts.rag_answer_prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger("marksheet.claude")

# Short, fixed safety notes returned alongside every Claude answer.
_SAFETY_NOTES = [
    "This explanation is generated from local policy context and case evidence only.",
    "It is a review aid, not a decision — a human reviewer makes the final call.",
    "The assistant cannot change the risk score, status, reports, or any decision.",
    "Official verification is stronger than any signal from this system.",
]

# Cache the client between requests (created on first successful use).
_client = None


def _get_client():
    """
    Return a cached Anthropic client, creating it lazily. Returns None if no API
    key is configured or the anthropic package is unavailable. Never raises.
    """
    global _client
    if _client is not None:
        return _client
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic  # imported lazily so the app runs without the package

        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return _client
    except Exception:  # noqa: BLE001 - missing package / bad init -> use fallback
        return None


def _unavailable(error: str) -> dict:
    return {
        "available": False,
        "mode": "local_fallback_required",
        "model": config.ANTHROPIC_MODEL,
        "answer": None,
        "safety_notes": list(_SAFETY_NOTES),
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "error": error,
    }


def generate_claude_rag_answer(
    question: str,
    retrieved_sources: list[dict],
    case_summary: Optional[dict] = None,
) -> dict:
    """
    Ask Claude to answer `question` using the retrieved policy chunks (and an
    optional case summary). Returns a structured dict; never raises.

    On success:  {"available": True, "mode": "claude_rag", "model": ..., "answer": ...,
                  "safety_notes": [...], "usage": {...}, "error": None}
    On failure:  {"available": False, "mode": "local_fallback_required", "answer": None,
                  "error": "..."}
    """
    if not config.ANTHROPIC_API_KEY:
        return _unavailable("ANTHROPIC_API_KEY is not configured.")

    client = _get_client()
    if client is None:
        return _unavailable("Anthropic client unavailable (package missing or init failed).")

    try:
        user_prompt = build_user_prompt(question, retrieved_sources, case_summary)
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.LLM_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Concatenate the text blocks of the response.
        answer = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()

        if not answer:
            return _unavailable("Claude returned an empty response.")

        usage = getattr(response, "usage", None)
        return {
            "available": True,
            "mode": "claude_rag",
            "model": config.ANTHROPIC_MODEL,
            "answer": answer,
            "safety_notes": list(_SAFETY_NOTES),
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", 0) if usage else 0,
                "output_tokens": getattr(usage, "output_tokens", 0) if usage else 0,
            },
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - any API error -> graceful fallback
        # Note: we surface only the error type + message, never the API key.
        logger.warning("Claude call failed; using local fallback: %s", type(exc).__name__)
        return _unavailable(f"{type(exc).__name__}: {exc}")
