# Marksheet Verifier — Technical Whitepaper

**AI-assisted academic document verification and tampering-signal analysis**

**Author:** Purvaj Gaonkar
**Institution:** Vidyalankar Institute of Technology· **Year:** 2026

**Live demo:** https://marksheet-verifier-hazel.vercel.app
**API health:** https://marksheet-verifier-backend.onrender.com/health
**Source:** https://github.com/purvajgaonkar/marksheet-verifier

> ⚠️ This system produces **evidence-based risk signals for human reviewers** — it
> never automatically accuses or rejects a student. Every report carries the
> disclaimer: *"MVP signal report, not final proof of tampering."*

---

## 1. Overview

Marksheet Verifier is a full-stack, AI-assisted platform that helps university
admissions teams **triage** uploaded academic marksheets. A student uploads a
marksheet (PDF/JPG/PNG); the system runs OCR, inspects file metadata, performs
pixel-level image forensics, orchestrates a set of rule-based "agents", computes
a transparent **risk score**, and can generate a plain-English, source-grounded
explanation using the Claude API. A reviewer sees all of this on an admin
dashboard and records the **final human decision**, which is written to an
append-only audit trail.

The project was built in **11 incremental phases**, from an offline command-line
analyzer to a deployed, authenticated, multi-role web application — with a
deliberate emphasis on **explainability, safety, and honest engineering
tradeoffs**.

## 2. Problem

Forged or altered marksheets are a real risk in admissions, but fully automated
"fraud detection" is both technically unreliable and ethically dangerous — a
false positive can unfairly harm a genuine student. The goal here is **not** to
auto-decide, but to **prioritise** which documents a human should scrutinise, and
to make every signal **transparent and contestable**.

## 3. What it does

**Student portal**
- Register / log in, upload a marksheet, and track submission status.
- Sees **only safe statuses** (submitted / under review / verified / re-upload
  required / …) — never the internal risk score or forensic details.

**Admin / reviewer portal**
- Dashboard of all cases with risk labels and OCR confidence.
- Case detail: extracted fields, metadata flags, **image-forensics heatmaps**, a
  step-by-step **agentic workflow trace**, a transparent risk breakdown, an
  optional **Claude explanation**, a **human decision panel**, and the **audit
  trail**.
- A local **RAG policy assistant** answers reviewer questions with cited sources.

## 4. System architecture

```
        Browser (React + Vite, Tailwind)
                    |  HTTPS, JWT bearer, CORS-restricted
                    v
        FastAPI backend (Python)
   ┌───────────────┼─────────────────────────────┐
   v               v                             v
 Analysis      Auth + RBAC                 RAG assistant
 pipeline      (JWT, bcrypt)               (TF-IDF retrieval
   |                                        + optional Claude)
   ├── OCR (Tesseract)                          |
   ├── Metadata (ExifTool)                      v
   ├── Image forensics (OpenCV: ELA/edge/    Anthropic Claude API
   │   noise/anomaly heatmap)                 (optional; graceful
   ├── Rule-based multi-agent orchestration   local fallback)
   └── Transparent risk scoring
                    |
                    v
        SQLAlchemy ORM  ──►  PostgreSQL (Supabase) / SQLite (local)
        Files + JSON reports on disk / object storage (future)
                    |
                    v
        Append-only audit trail (who did what, when)
```

**Deployed topology:** React frontend on **Vercel** → FastAPI backend on
**Render** (Dockerized to include the Tesseract/ExifTool toolchain) → **Supabase**
PostgreSQL → optional **Claude API**.

## 5. Technology stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Framer Motion, lucide-react |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| OCR / docs | Tesseract OCR (pytesseract), PyMuPDF, Pillow, OpenCV, NumPy |
| Metadata | ExifTool |
| AI / RAG | scikit-learn (TF-IDF retrieval), Anthropic Claude API (optional) |
| Data | SQLAlchemy ORM; PostgreSQL (Supabase) / SQLite; JSON reports |
| Auth | JWT (python-jose), bcrypt (passlib), role-based access control |
| Deploy | Vercel, Render (Docker), Supabase; environment-driven config |

## 6. How the analysis works

The pipeline is organised as a **local, deterministic multi-agent workflow** —
each agent has one responsibility, and the orchestrator records a full trace:

1. **OCR Agent** — extracts text and per-field values (board, roll number, total
   marks, percentage) with a confidence score.
2. **Metadata Agent** — reads EXIF/PDF metadata and flags editing software
   (Photoshop, Canva, GIMP…), suspicious producers, and create/modify date
   mismatches.
3. **Forensics Agent** — runs pixel-level checks (Error-Level Analysis, edge and
   noise maps, a combined anomaly heatmap). Deliberately treated as a **weak
   signal**, capped so it can nudge but never dominate the score.
4. **Rule Validation Agent** — checks basic document expectations (fields
   present, plausible values).
5. **Decision Agent** — combines all signals into a transparent **risk score**
   (0–1) and one of six labels (`verified → low → medium → needs_review → high`,
   plus `unable_to_verify`), each with a plain-English reason.

The risk model is an **intentionally transparent weighted heuristic**, not a
black-box classifier — every point added to the score is explained in the report,
so a reviewer (or student) can understand and challenge it.

**Optional Claude layer:** when enabled, Claude produces a source-grounded,
plain-English explanation of a case and answers reviewer policy questions via
retrieval-augmented generation over local policy documents. If the API is
disabled or fails, the system **falls back to a local model automatically** — it
never breaks.

## 7. Engineering highlights

Beyond the feature set, the build surfaced several real-world problems worth
noting (recruiters: these show debugging + systems thinking):

- **Explainable-by-design AI:** a deterministic agent pipeline + transparent risk
  weights, chosen over an opaque ML classifier so every decision is auditable.
- **Graceful degradation:** the Claude integration always has a local fallback;
  missing metadata or failed forensics never crash a run.
- **Dockerized OCR toolchain:** the deployment needs system binaries (Tesseract,
  ExifTool) and OpenCV's shared libraries that a native Python host can't
  install — solved with a Docker image whose build context is the repo root so
  it ships both the backend and the RAG policy docs.
- **Free-tier constraint solving:** diagnosed and fixed production issues end to
  end — Supabase's IPv6-only direct host (switched to the IPv4 session pooler),
  `postgres://`→`postgresql://` URL normalization, and a health-check restart
  loop caused by CPU-heavy forensics on a 0.1-CPU instance (added a
  `FORENSICS_ENABLED` toggle to disable the heaviest step in production while
  keeping full analysis locally).
- **Environment-driven configuration:** no hardcoded URLs or secrets; CORS,
  database, upload limits, and JWT all come from environment variables.

## 8. Security & access control

- **JWT authentication** with **bcrypt**-hashed passwords.
- **Role-based access control:** `student` vs `admin`/`reviewer`; students can
  only see their **own** submissions and never internal risk data.
- **Protected routes** on both API and UI; **no token → 401**, wrong role → **403**.
- **Upload validation:** extension allow-list, size limit, empty-file rejection,
  filename sanitisation, and **magic-byte content sniffing** (a renamed
  executable can't masquerade as a PDF).
- **One-time admin bootstrap** endpoint gated by a setup secret; secrets live only
  in environment variables and are never committed.

## 9. Deployment

The app is deployed on free tiers with fully environment-driven configuration
(see `docs/DEPLOYMENT_GUIDE.md`): Vercel (frontend), Render (Dockerized backend),
Supabase (PostgreSQL). SQLite remains the zero-setup local default; switching to
PostgreSQL is a single `DATABASE_URL` change.

## 10. Responsible design (ethics & limitations)

- **Signals, not verdicts.** The system prioritises human review; a human makes
  every final decision.
- **Students never see internal AI details** — only safe, non-accusatory statuses.
- **Weak signals are labelled as weak.** Pixel forensics and metadata flags have
  many benign causes (compression, scanning, re-saving, messaging apps), so the
  system never overclaims, and forensics is capped in the score.
- **Official verification is stronger** than any image signal; board / DigiLocker /
  NAD verification is the correct path for high-stakes decisions (out of scope
  for this MVP).
- **Known limitations:** OCR accuracy varies with scan quality; the risk model is
  a heuristic, not a trained fraud detector; free-tier hosting is slow and its
  local file storage is ephemeral.

## 11. Future work

- Object storage (S3 / R2 / Supabase Storage) for durable uploads.
- Background worker so full forensics runs at scale without blocking requests.
- Official board / DigiLocker verification integration.
- Optional trained model as an *additional* signal alongside the transparent
  heuristic.

---

*Built as an incremental, phase-by-phase engineering project (Phases 1–11): CLI
analyzer → API → UI → forensics → agentic orchestration → RAG → Claude → database
& workflow → authentication → production hardening → deployment. See the repo
README and `docs/PROJECT_PLAN.md` for the full breakdown.*
