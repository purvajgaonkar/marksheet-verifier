"""
rag_service.py
==============

The local RAG (Retrieval-Augmented Generation) orchestrator for the Policy
Assistant. It:

  1. (optionally) loads a short summary of a specific case,
  2. retrieves the most relevant policy chunks from the knowledge base,
  3. composes a concise, reviewer-friendly answer from the retrieved text using
     deterministic templates (NO LLM / NO external API),
  4. returns the answer plus the sources used and a limitations note.

Answers are EXTRACTIVE: they are built from sentences that actually appear in
the project's policy documents, so the assistant never invents policy.
"""

from __future__ import annotations

import json
import re

from app import config
from app.rag.knowledge_base import get_knowledge_base
from app.services import retrieval_service

MODE = "local_retrieval_template"

LIMITATIONS = [
    "This assistant uses local policy documents only.",
    "It does not make final admission decisions.",
    "Retrieved policy text may be incomplete — review the cited sources.",
    "Human review is required for high-risk cases; official verification is stronger than any signal.",
]

# How many chunks to retrieve and how many sentences to keep in the answer.
_TOP_K = 5
_ANSWER_SENTENCES = 3

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_HEADING_PREFIX = re.compile(r"^\[[^\]]*\]\s*")

# Map fancy unicode punctuation to plain ASCII so answers render cleanly
# everywhere (terminals, JSON, the React UI).
_PUNCT_MAP = {
    "—": "-", "–": "-", "’": "'", "‘": "'",
    "“": '"', "”": '"', "…": "...", " ": " ",
}


def _normalize_punct(text: str) -> str:
    for bad, good in _PUNCT_MAP.items():
        text = text.replace(bad, good)
    return text


def _clean_markdown(text: str) -> str:
    """Strip markdown formatting so extracted sentences read as plain prose."""
    text = _normalize_punct(text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)          # blockquotes
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)      # headings
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)       # bullet lists
    text = re.sub(r"(?m)^\s*\d+\.\s+", "", text)       # numbered lists
    text = text.replace("**", "").replace("*", "").replace("`", "")  # emphasis / code
    text = re.sub(r"\s+", " ", text)                    # collapse whitespace
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_sources() -> dict:
    """List indexed documents (for GET /rag/sources)."""
    return get_knowledge_base().sources()


def reindex() -> dict:
    """Rebuild the in-memory index from docs/ (for POST /rag/reindex)."""
    return get_knowledge_base().reindex()


def answer_question(question: str, case_id: str | None = None) -> dict:
    """
    Answer a reviewer question using local policy docs, optionally case-aware.

    Returns the structured response described in the Phase 6 spec.
    """
    question = (question or "").strip()
    if not question:
        return {
            "question": question,
            "answer": "Please enter a question for the policy assistant.",
            "sources": [],
            "case_summary": None,
            "mode": MODE,
            "limitations": list(LIMITATIONS),
        }

    case_summary = _load_case_summary(case_id) if case_id else None

    kb = get_knowledge_base()
    chunks = kb.search(question, top_k=_TOP_K)

    answer = _compose_answer(question, chunks, case_summary)

    sources = [
        {"document": c["document"], "chunk_id": c["chunk_id"], "preview": c["preview"]}
        for c in chunks
    ]

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "case_summary": case_summary,
        "mode": MODE,
        "limitations": list(LIMITATIONS),
    }


# ---------------------------------------------------------------------------
# Case summary
# ---------------------------------------------------------------------------
def _load_case_summary(case_id: str) -> dict | None:
    """
    Build a short summary of a case from its report JSON. Returns None (with no
    error) if the report cannot be found, so the assistant still answers from
    policy alone.
    """
    report_path = config.REPORTS_DIR / f"{case_id}_report.json"
    if not report_path.is_file():
        return {
            "case_id": case_id,
            "found": False,
            "note": "No report was found for this case id.",
        }
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError):
        return {
            "case_id": case_id,
            "found": False,
            "note": "The report for this case could not be read.",
        }

    risk = report.get("risk", {})
    ocr = report.get("ocr", {})
    metadata = report.get("metadata", {})
    forensics = report.get("image_forensics", {})
    workflow = report.get("agentic_workflow", {})
    recommendation = workflow.get("recommendation", {}) if isinstance(workflow, dict) else {}

    flags = metadata.get("flags", []) or []
    anomaly = forensics.get("anomaly_score") if forensics.get("available") else None

    return {
        "case_id": case_id,
        "found": True,
        "risk_label": risk.get("label"),
        "risk_score": risk.get("score"),
        "ocr_confidence": ocr.get("average_confidence"),
        "metadata_flag_count": len(flags),
        "metadata_flags": flags,
        "forensics_anomaly_score": anomaly,
        "human_review_required": recommendation.get("human_review_required"),
        "recommendation": recommendation.get("recommendation"),
        "contributing_factors": risk.get("contributing_factors", []),
    }


def _case_summary_sentence(summary: dict) -> str:
    """Render a one/two-sentence plain-English summary of a case."""
    if not summary or not summary.get("found"):
        note = (summary or {}).get("note", "No case details were available.")
        return note

    parts = [
        f"This case ({summary['case_id']}) is currently labeled "
        f"{summary.get('risk_label', 'unknown')} with a risk score of "
        f"{summary.get('risk_score', 'n/a')}."
    ]
    detail = []
    if summary.get("ocr_confidence") is not None:
        detail.append(f"OCR confidence was {summary['ocr_confidence']}/100")
    count = summary.get("metadata_flag_count", 0)
    detail.append(
        f"{count} metadata warning{'' if count == 1 else 's'} were found"
    )
    if summary.get("forensics_anomaly_score") is not None:
        detail.append(
            f"the image-forensics anomaly score was {summary['forensics_anomaly_score']} (weak evidence)"
        )
    if detail:
        parts.append(", ".join(detail) + ".")
    if summary.get("recommendation"):
        parts.append(f"Workflow recommendation: {summary['recommendation']}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Answer composition (extractive + template)
# ---------------------------------------------------------------------------
def _is_quality_sentence(s: str) -> bool:
    """
    Keep readable prose; drop table rows, diagram residue, and fragments.
    A good sentence is long enough, mostly letters, and has several words.
    """
    if len(s) <= 25:
        return False
    if "|" in s:  # markdown table / ASCII diagram residue
        return False
    letters = sum(c.isalpha() or c.isspace() for c in s)
    if letters / len(s) < 0.7:
        return False
    if len(s.split()) < 4:
        return False
    # A well-formed sentence starts with a capital letter or digit. A leading
    # lowercase letter usually means we captured a mid-sentence fragment.
    first_alpha = next((c for c in s if c.isalpha()), "")
    if first_alpha and first_alpha.islower():
        return False
    return True


def _split_sentences(text: str) -> list[str]:
    cleaned = _HEADING_PREFIX.sub("", text.strip())
    cleaned = _clean_markdown(cleaned)
    sentences = [s.strip(" -*") for s in _SENTENCE_SPLIT.split(cleaned)]
    # Keep substantive, readable sentences only.
    return [s for s in sentences if _is_quality_sentence(s)]


def _select_policy_sentences(question: str, chunks: list[dict]) -> list[str]:
    """Pick the most relevant, de-duplicated sentences from the top chunks."""
    sentences: list[str] = []
    for chunk in chunks[:3]:
        sentences.extend(_split_sentences(chunk["text"]))

    if not sentences:
        return []

    ranked = retrieval_service.score_sentences(question, sentences)
    picked: list[str] = []
    seen: set[str] = set()
    for index, _score in ranked:
        sentence = sentences[index]
        # The bare MVP disclaimer is already stated in the closing reminder, so
        # skip it here to avoid repetition.
        if "not final proof of tampering" in sentence.lower():
            continue
        # De-duplicate near-identical sentences by their significant tokens.
        key = " ".join(sorted(set(retrieval_service.tokenize(sentence))))[:80]
        if key in seen:
            continue
        seen.add(key)
        picked.append(sentence)
        if len(picked) >= _ANSWER_SENTENCES:
            break
    return picked


def _compose_answer(question: str, chunks: list[dict], case_summary: dict | None) -> str:
    parts: list[str] = []

    # 1) Case context, if a case was provided.
    if case_summary is not None:
        parts.append(_case_summary_sentence(case_summary))

    # 2) Policy guidance, extracted from the retrieved documents.
    policy_sentences = _select_policy_sentences(question, chunks)
    if policy_sentences:
        guidance = " ".join(
            s if s.endswith((".", "!", "?")) else s + "." for s in policy_sentences
        )
        prefix = (
            "According to the project's policy documents, "
            if case_summary is None
            else "According to the reviewer guidelines, "
        )
        parts.append(prefix + guidance[0].lower() + guidance[1:])
    else:
        parts.append(
            "I could not find specific guidance for that question in the local "
            "policy documents. Try rephrasing, or review the documents directly."
        )

    # 3) Standard, non-accusatory closing reminder.
    parts.append(
        "Remember: these are risk signals and weak evidence only - the final "
        "decision requires a human reviewer, and official verification is "
        "stronger than any signal from this system."
    )

    return _normalize_punct(" ".join(parts))
