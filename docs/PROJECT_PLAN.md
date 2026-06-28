# Project Plan — Marksheet Verifier

An agentic-AI-inspired marksheet verification and tampering-signal detection
system for university admissions. It produces **evidence-based risk signals**
for human reviewers — it never auto-accuses or auto-rejects a student.

> Every report carries: *"This is an MVP signal report, not final proof of tampering."*

---

## Phases

| Phase | Status | What it adds |
|-------|--------|--------------|
| 1 | ✅ | Command-line analyzer: OCR, metadata, risk report |
| 2 | ✅ | FastAPI backend: upload, cases, reports (local JSON store) |
| 3 | ✅ | Polished React + Vite frontend (dashboard, case detail) |
| 4 | ✅ | Image/pixel forensics (ELA, edge, sharpness, noise, anomaly heatmap) |
| 5 | ✅ | Local rule-based agentic orchestration |
| 6 | ✅ | **Local RAG policy assistant** (this phase) |
| 7 | ⬜ | `/metrics` endpoint for Prometheus |
| 8 | ⬜ | Docker + Prometheus + Grafana |

No external AI/LLM API, Docker, Prometheus, Grafana, PostgreSQL, Redis, or auth
is required for Phases 1–6. Everything runs locally.

---

## Phase 5 architecture — local agentic workflow

The analysis is organised as a set of **local, rule-based agents**, each with a
single responsibility, coordinated by an **Orchestrator**. There is no LLM and
no external API — the "agents" are deterministic Python modules that reuse the
existing services.

```
                     Student Upload (PDF / JPG / PNG)
                                 |
                                 v
                         +---------------+
                         |  Orchestrator |   run_id, timings, trace
                         +---------------+
                                 |
     critical input prep: validate file -> check tools -> render PDF -> preprocess
                                 |
        +------------+-----------+-----------+------------------+
        v            v           v           v                  v
   +---------+  +----------+ +-----------+ +----------------+ +-----------+
   |  OCR    |  | Metadata | | Forensics | | Rule Validation| | Decision  |
   |  Agent  |  |  Agent   | |   Agent   | |     Agent      | |   Agent   |
   +---------+  +----------+ +-----------+ +----------------+ +-----------+
        |            |            |               |                |
   text +       ExifTool     ELA/edge/        deterministic   aggregate +
   confidence    flags       sharpness/        field rules    risk_service
   + fields                  noise/heatmap                    -> recommendation
        \____________\____________\______________\________________/
                                 |
                                 v
                    +-----------------------------+
                    |   Evidence Report (JSON)    |
                    |  risk + image_forensics +   |
                    |  agentic_workflow trace     |
                    +-----------------------------+
                                 |
                                 v
                          Human Review
                 (final decision — always a person)
```

### Agents

1. **OCR Agent** — runs Tesseract via `ocr_service`; returns text, confidence,
   and detected fields (board, roll number, total marks, percentage, result).
2. **Metadata Agent** — runs ExifTool via `metadata_service`; returns metadata
   warning flags (editor software, date mismatch, suspicious producer). *A
   metadata warning is not proof of tampering.*
3. **Forensics Agent** — runs Phase 4 `forensics_service`; returns the weak
   anomaly score and visualization paths. *Pixel forensics are weak signals only.*
4. **Rule Validation Agent** — deterministic checks on the OCR fields (missing
   roll number / total / result keyword, percentage range, marks reasonableness).
5. **Decision Agent** — aggregates all evidence, calls `risk_service` for the
   final score/label, and produces a non-accusatory recommendation plus a
   `human_review_required` flag.

### Orchestrator responsibilities

- Assigns a unique `run_id`.
- Runs **critical input prep** first; only this can abort the whole run.
- Runs the five agents in order, collecting a **trace** (each agent's standard
  result envelope: status, duration, summary, findings, warnings, errors).
- **Continues even if a weak agent fails** (e.g. forensics) — that agent is
  marked `failed`/`completed_with_warnings` and the workflow proceeds.
- Writes the full `agentic_workflow` block into the report JSON.

### Why no API key is needed

The agents are local rule-based modules. They reuse Tesseract, ExifTool, OpenCV,
Pillow, NumPy, and PyMuPDF — all installed locally. No Claude/OpenAI/Gemini/
Hugging Face/DigiLocker API is called. (Claude Code, used to *build* this
project, is unrelated to the project's runtime and requires no project API key.)

---

## Phase 6 architecture — local RAG policy assistant

A reviewer can ask plain-English questions ("Why is this case needs_review?",
"Are pixel forensics proof?") and get answers grounded in the project's own
policy documents. It is **fully local**: a TF-IDF index over `docs/` plus a
deterministic template answer generator. No LLM, no external API, no API key.

```
        Reviewer Question (+ optional case_id)
                       |
                       v
                  +-----------+
                  | RAG Route |   POST /rag/ask
                  +-----------+
                       |
       +---------------+-----------------+
       v                                 v
  Case Summary Loader (optional)    Document Loader (docs/*.md -> chunks)
  (risk, OCR, flags, anomaly,            |
   human-review recommendation)         v
       |                          Local Retriever (TF-IDF, scikit-learn)
       |                                 |  top chunks
       +---------------+-----------------+
                       v
            Template Answer Generator
       (extractive sentences + case context,
        non-accusatory wording, always cites sources)
                       |
                       v
              Sources + Answer (JSON)
                       |
                       v
            Frontend Policy Assistant (/assistant)
```

Endpoints: `POST /rag/ask`, `GET /rag/sources`, `POST /rag/reindex`. Knowledge
documents: `PROJECT_PLAN.md`, `ETHICS_AND_LIMITATIONS.md`, `API_REQUIREMENTS.md`,
`REVIEWER_GUIDELINES.md`, `RAG_POLICY_KNOWLEDGE.md`.

---

## Current limitations

- Field detection and rule validation are simple/regex-based and miss unusual
  layouts; they feed **weak signals** only.
- The risk score is a transparent heuristic for **prioritisation**, never an
  automatic decision.
- Metadata and pixel signals have many innocent causes (scanning, compression,
  messaging apps, PDF conversion).
- No official board / DigiLocker / NAD verification yet — that is stronger than
  any signal produced here and is out of scope for the MVP.
- Reviewer decisions in the UI are stored in the browser only (not persisted).
