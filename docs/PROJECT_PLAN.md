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
| 6 | ✅ | Local RAG policy assistant |
| 7 | ✅ | Optional Claude API RAG + explanation |
| 8 | ✅ | Database + student/admin workflow + audit trail |
| 9 | ✅ | **Authentication + role-based access control** (this phase) |
| 10 | ⬜ | `/metrics` endpoint for Prometheus |
| 11 | ⬜ | Docker + Prometheus + Grafana |

Phases 1–6 require no external AI/LLM API at all. Phase 7 adds an **optional**
Claude mode. Phase 8 adds a SQLAlchemy database (SQLite by default,
PostgreSQL-ready) plus a student/admin workflow and an audit trail. Phase 9 adds
email/password authentication with JWT access tokens and role-based access
control (student vs admin/reviewer). No Docker, Prometheus, Grafana, Redis, MCP,
or external identity provider is required through Phase 9.

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

## Phase 7 architecture — optional Claude API mode

Phase 7 adds an **optional** Claude-powered answer generator on top of the same
local retrieval. It is controlled entirely by environment variables in
`backend/.env`; with no key (or the switch off) the app uses the Phase 6 local
fallback. No API key is hardcoded or committed.

```
   Reviewer Question  /  Case Explanation Request
                       |
                       v
                 RAG Retriever (local TF-IDF over docs/)
                       |
        +--------------+--------------------+
        v                                   v
  Case Summary Loader (optional)      Prompt Builder (safety rules +
  (risk, OCR, flags, anomaly,          injection defence; OCR/question
   agents, recommendation)             treated as UNTRUSTED data)
        |                                   |
        +--------------+--------------------+
                       v
            LLM_ENABLED and ANTHROPIC_API_KEY?
                /                    \
             yes                      no
              v                        v
        Claude API            Local Template Answer
     (claude_service)          (Phase 6 fallback)
              |   on failure ........> |
              v                        v
        Safe Explanation  <-----------+
                       |
                       v
       Sources + Answer (mode, model, llm_available, llm_error)
                       |
                       v
     Frontend: Policy Assistant (/assistant) + Case Detail "Generate
     LLM Explanation". Answer carries a mode badge (Claude-powered RAG /
     Local fallback) and never shows the API key.
```

Endpoints: `GET /rag/llm-status`, `POST /cases/{case_id}/explain`, and the
enriched `POST /rag/ask`. Safety: Claude is an explanation aid only — it cannot
change the risk score, status, reports, or any reviewer decision.

---

## Phase 8 architecture — database + workflow + audit trail

Phase 8 turns the project into a small credential-verification platform: a real
persistence layer (SQLAlchemy; SQLite by default, PostgreSQL-ready), a separate
student vs admin workflow, and an append-only audit trail. The JSON report flow
is unchanged — the database is an additional structured store that holds case
metadata and FILE PATHS (never raw bytes).

```
  Student Upload (name, email, application id, board, year, file)
        |
        v
   FastAPI  /student/submit
        |
        v
   AI Analysis Pipeline (Phases 1-5: OCR, metadata, forensics, agents)
        |
        +--> uploads/<case>.png        (file on disk, unchanged)
        +--> reports/<case>.json       (report on disk, unchanged)
        |
        v
   Database Case record  + StudentSubmission + AuditLog
   (case_id, status, admin_risk_label, risk_score, ocr_confidence,
    metadata_flag_count, forensics_score, file_path, report_path)
        |
        +------------------ Safe Student Status ------------------+
        |  GET /student/submission/{id}                           |
        |  -> status + message + action (NO risk details shown)   |
        |                                                         |
        v                                                         v
   Admin Review Dashboard  (GET /admin/cases, /admin/cases/{id})   Student portal
        |  full signals, report, agent trace, forensics, history
        v
   Human Decision  (POST /admin/cases/{id}/decision)
        |  decision + reviewer comment + new student-facing status
        v
   Audit Log  (document_uploaded, analysis_*, status_updated, review_decision)
        |
        v
   Student sees the updated SAFE status on next tracking check.
```

Tables: `users`, `cases`, `student_submissions`, `review_decisions`,
`audit_logs`. The system never auto-decides — only the human reviewer endpoint
changes a case outcome.

---

## Phase 9 architecture — authentication + role-based access control

Phase 9 secures the workflow with email/password login, JWT access tokens, and
role checks. Passwords are hashed (bcrypt via passlib); tokens are signed JWTs
(python-jose) carrying the user id and role.

```
  User → Login / Register
        |
        v
   FastAPI Auth Routes  (/auth/register, /auth/login, /auth/me)
        |
        +--> Register: hash password (bcrypt)  → store User(role=student)
        |
        +--> Login: verify password → issue JWT { sub: user_id, role }
        |
        v
   Frontend stores JWT (localStorage) and sends it as
   "Authorization: Bearer <token>" on every protected request
        |
        v
   Auth dependency: decode JWT → load active User → enforce ROLE
        |
        +───────────────┬───────────────────────────────┐
        v               v                                v
   require_student   require_admin_or_reviewer      (no/invalid token)
        |               |                                |
        v               v                                v
   Student Portal    Admin / Reviewer Portal           401 Unauthorized
   - submit (own)    - list all cases                  (student → admin = 403)
   - my submissions  - case detail + signals
   - track own case  - record human decision
   (safe data only)  - audit trail
```

Roles: `student` (self-registered) and `admin` / `reviewer` (created server-side
via `backend/create_admin.py`). Students only ever see safe statuses; internal AI
risk details are admin/reviewer-only. Authentication changes *who sees what* — it
does not let the AI decide; a human reviewer's recorded decision is still the only
thing that changes a case outcome.

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
