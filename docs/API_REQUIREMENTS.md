# API Requirements

What external services and API keys this project needs — and, importantly, what
it does **not** need. The MVP runs entirely locally.

---

## Summary

| Capability | Needed for MVP? | Notes |
|------------|-----------------|-------|
| Claude API (Anthropic) | ❌ No | Not used at runtime. Optional future "LLM mode". |
| OpenAI / Gemini / Hugging Face API | ❌ No | Not used. |
| DigiLocker / NAD / board API | ❌ No (future) | Needed only for *official* verification later. |
| Paid cloud OCR | ❌ No | Local Tesseract is used instead. |
| Local Tesseract OCR | ✅ Yes | Reads text from images. External program, not a pip package. |
| Local ExifTool | ✅ Yes | Reads file metadata. External program, not a pip package. |

- **Claude API is NOT required for the MVP.** The analysis pipeline, agents, and
  RAG assistant all run with local tools only.
- **Claude Code login is separate from project API usage.** Claude Code may be
  used to *build* this project; that is unrelated to the project's runtime and
  requires no project API key.
- **DigiLocker / NAD / board APIs may be needed later** for official
  verification, which is stronger than any signal this system produces.
- **Paid OCR APIs are optional, not required.** Local Tesseract is used for the MVP.

---

## Phase 6 RAG API Requirements

The Phase 6 Policy Assistant is a **local Retrieval-Augmented Generation (RAG)**
feature. It answers reviewer questions using only the project's own policy
documents in `docs/`.

- **No external API key is required for local RAG.** Retrieval uses a local
  TF-IDF index (scikit-learn) built from the `docs/` markdown files; answers are
  generated from the retrieved text using deterministic templates.
- **Local retrieval uses `docs/` markdown files** — `PROJECT_PLAN.md`,
  `ETHICS_AND_LIMITATIONS.md`, `API_REQUIREMENTS.md`, `REVIEWER_GUIDELINES.md`,
  and `RAG_POLICY_KNOWLEDGE.md`. Edit those docs and call `POST /rag/reindex` to
  refresh the index.
- **An optional future LLM mode** could use a Claude or OpenAI API key to phrase
  answers more naturally on top of the same retrieved context. This is **not**
  enabled now and is not required.
- **The app must work even without any LLM key.** If no LLM is configured, the
  assistant falls back to (and currently always uses) local
  `local_retrieval_template` answers.

### Phase 6 endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/rag/ask` | Answer a reviewer question (optionally case-aware) |
| `GET`  | `/rag/sources` | List indexed documents + chunk count + retrieval mode |
| `POST` | `/rag/reindex` | Rebuild the in-memory index from `docs/` |

`POST /rag/ask` accepts `{ "question": "...", "case_id": "optional" }` and returns
an answer, the source chunks used, a `mode` of `local_retrieval_template`, and a
list of limitations.
