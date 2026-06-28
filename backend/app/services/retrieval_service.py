"""
retrieval_service.py
====================

Local, in-memory retrieval over the document chunks. Two backends:

  * TF-IDF (preferred) using scikit-learn — ranks chunks by cosine similarity.
  * Keyword overlap (fallback) — used only if scikit-learn is not installed,
    so the assistant still works on a minimal environment.

Everything is local. No network, no vector database, no API key.
"""

from __future__ import annotations

import math
import re
from collections import Counter

# Try scikit-learn; fall back gracefully if it is unavailable.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    _SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover - only when sklearn missing
    _SKLEARN_AVAILABLE = False


_TOKEN_RE = re.compile(r"[a-z0-9_]+")

# A small English stop-word list for the keyword fallback / sentence scoring.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was", "were",
    "for", "on", "with", "as", "by", "it", "this", "that", "these", "those",
    "be", "been", "being", "at", "from", "what", "why", "how", "do", "does",
    "should", "i", "you", "we", "they", "if", "not", "no", "can", "will", "may",
    "about", "into", "than", "then", "when", "which", "who", "whom", "but",
}


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens with stop-words removed (used by the fallback)."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


class _TfidfBackend:
    mode = "local_tfidf"

    def __init__(self, texts: list[str]):
        # sublinear_tf + english stop words give solid results on short docs.
        self.vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(texts)

    def query(self, question: str, top_k: int) -> list[tuple[int, float]]:
        q_vec = self.vectorizer.transform([question])
        scores = linear_kernel(q_vec, self.matrix).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in ranked if scores[i] > 0.0]


class _KeywordBackend:
    mode = "local_keyword"

    def __init__(self, texts: list[str]):
        self.doc_tokens = [Counter(tokenize(t)) for t in texts]
        # Inverse document frequency for light weighting.
        n = len(texts) or 1
        df: Counter = Counter()
        for counts in self.doc_tokens:
            for token in counts:
                df[token] += 1
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    def query(self, question: str, top_k: int) -> list[tuple[int, float]]:
        q_tokens = tokenize(question)
        if not q_tokens:
            return []
        scored = []
        for i, counts in enumerate(self.doc_tokens):
            score = 0.0
            for token in q_tokens:
                if token in counts:
                    score += counts[token] * self.idf.get(token, 1.0)
            if score > 0:
                scored.append((i, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def build_retriever(texts: list[str]):
    """
    Build a retriever over the given chunk texts. Returns an object with a
    `.mode` string and a `.query(question, top_k)` method that yields
    (chunk_index, score) tuples, highest score first.
    """
    if not texts:
        return _KeywordBackend([])
    if _SKLEARN_AVAILABLE:
        return _TfidfBackend(texts)
    return _KeywordBackend(texts)


def score_sentences(query: str, sentences: list[str]) -> list[tuple[int, float]]:
    """
    Lightweight extractive scorer used to pick the most relevant sentences from
    retrieved chunks for the template answer. Uses idf-free token overlap, which
    is robust and needs no model.
    """
    q_tokens = set(tokenize(query))
    if not q_tokens:
        return []
    scored = []
    for i, sentence in enumerate(sentences):
        s_tokens = tokenize(sentence)
        if not s_tokens:
            continue
        overlap = sum(1 for t in s_tokens if t in q_tokens)
        if overlap:
            # Normalise a little by sentence length so very long sentences do
            # not always win.
            scored.append((i, overlap / math.sqrt(len(s_tokens))))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
