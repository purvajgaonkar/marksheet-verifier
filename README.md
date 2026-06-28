# marksheet-verifier

An **agentic-AI-inspired marksheet verification and tampering-signal detection
system** for university admissions (final-year project / MVP).

Students upload their Class 10 / 12 marksheets (PDF / JPG / PNG). The system
extracts text (OCR), reads file metadata, runs basic image checks, and produces
a **risk signal** so a **human reviewer** can prioritise which uploads to look
at closely.

> ⚠️ **This is an MVP signal report, not final proof of tampering.**
> The system **never** automatically accuses or rejects a student. It only
> produces evidence-based statuses, and a human always makes the final call.

### Risk statuses produced
`verified` · `low` · `medium` · `needs_review` · `high` · `unable_to_verify`

(`verified` means "no automated red flags found", **not** "officially verified
against the board".)

---

## Project status: Phases 1–10 complete (CLI + API + UI + forensics + agents + RAG + Claude + database + auth + deploy-prep)

The project is built in phases. **Phase 1** is the offline command-line
analyzer, **Phase 2** wraps the same pipeline in a FastAPI backend, **Phase 3**
adds a polished React + Vite dashboard, **Phase 4** adds local image/pixel
forensics, **Phase 5** reorganises the analysis as a local rule-based **agentic
workflow**, **Phase 6** adds a local **RAG policy assistant**, **Phase 7** adds an
**optional Claude API** answer mode, **Phase 8** adds a real **database +
student/admin workflow + audit trail**, **Phase 9** adds **authentication +
role-based access control** (JWT), and **Phase 10** is **production cleanup +
deployment preparation** (configurable env, safe CORS, upload validation, health
check, deployment-friendly admin setup). Actual deployment is Phase 11.

```
                 Phase 1: CLI analyzer            ✅
                 Phase 2: FastAPI backend         ✅
                 Phase 3: React frontend (Vite)   ✅
                 Phase 4: Pixel/image forensics   ✅
                 Phase 5: Agentic orchestration   ✅  (local rules, no external AI)
                 Phase 6: RAG policy assistant    ✅  (local TF-IDF, no API key)
                 Phase 7: Optional Claude API     ✅  (key optional; local fallback)
                 Phase 8: Database + workflow     ✅  (SQLite default; Postgres-ready)
                 Phase 9: Auth + RBAC (JWT)       ✅  (student vs admin/reviewer)
You are here ──► Phase 10: Production cleanup     ✅  (config, CORS, validation, /health)
                 Phase 11: Free-tier deployment
```

## Quick start (full stack)

Open **two terminals** from the project root.

**Terminal 1 — backend (FastAPI):**
```powershell
cd c:\Users\purva\Downloads\marksheet-verifier
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn app.main:app --reload --app-dir backend
```
- API:       http://127.0.0.1:8000
- API docs:  http://127.0.0.1:8000/docs

**Terminal 2 — frontend (React + Vite):**
```powershell
cd c:\Users\purva\Downloads\marksheet-verifier\frontend
npm install
npm run dev
```
- App:  http://localhost:5173

Then open **http://localhost:5173**, go to **Upload Marksheet**, choose
`uploads/dummy_marksheet.png` (or generate one — see below), and click
**Analyze marksheet**. The result links to the full case report, and the
**Admin Dashboard** lists every case.

> The frontend (`frontend/src/api.js`) talks to the backend at
> `http://127.0.0.1:8000`. CORS is pre-configured for `http://localhost:5173`
> and `http://localhost:3000`. Keep **both** servers running.

---

## What Phase 1 does

For one input file it will:

1. Validate the file (exists? supported type: `.pdf`, `.jpg`, `.jpeg`, `.png`?).
2. Locate and check **Tesseract OCR** and **ExifTool**.
3. If it is a PDF, render the **first page** to PNG (PyMuPDF).
4. Preprocess the image with **OpenCV** (grayscale → resize → denoise → adaptive threshold).
5. Run **OCR** (pytesseract) for full text + average confidence.
6. Detect simple fields: board, roll/seat number, total marks, percentage, result keyword.
7. Read **metadata** (ExifTool) and raise warning flags (Photoshop / Canva / GIMP / Illustrator-CorelDraw / PDF editor / date mismatch / missing dates / suspicious producer).
8. Compute a demo **risk score (0–1)** and a **risk label**.
9. Save a readable **JSON report** to `reports/`.
10. Save **intermediate debug images** to `forensic_outputs/`.
11. Print a terminal summary.

---

## Folder structure (Phase 1 parts in **bold**)

```
marksheet-verifier/
  backend/
    app/
      services/
        metadata_service.py          ** ExifTool metadata + warning flags
        ocr_service.py               ** pytesseract OCR + field detection
        pdf_service.py               ** PyMuPDF: render PDF page 1 to PNG
        image_preprocess_service.py  ** OpenCV preprocessing
        risk_service.py              ** risk score + label
        report_service.py            ** build/save/print the JSON report
      utils/
        command_checks.py            ** locate/verify Tesseract & ExifTool
    requirements.txt                 **
    analyze.py                       ** command-line entry point
  uploads/            (git-ignored)  put input files here
  reports/            (git-ignored)  generated JSON reports
  forensic_outputs/   (git-ignored)  debug/intermediate images
  sample_data/        dummy test data + generator
  docs/               project docs (added in later phases)
  README.md           **
  .gitignore          **
```

---

## Prerequisites

| Tool | Why | Notes |
|------|-----|-------|
| Python 3.10+ | runs the analyzer | tested on **3.13** |
| Tesseract OCR | reads text from images | external program, **not** a pip package |
| ExifTool | reads file metadata | external program, **not** a pip package |

> 💡 On Windows, these two tools are often installed but **not on PATH**, or PATH
> only updates after you re-open the terminal. This project handles that for you:
> it searches PATH first, then common install locations
> (e.g. `C:\Program Files\Tesseract-OCR\`, `C:\Tools\ExifTool\`).
> If yours are elsewhere, add the path to
> [`backend/app/utils/command_checks.py`](backend/app/utils/command_checks.py).

Install the external tools if you do not have them:
- **Tesseract (Windows):** https://github.com/UB-Mannheim/tesseract/wiki
- **ExifTool:** https://exiftool.org/ (download the Windows executable)

---

## Installation (Windows / PowerShell)

From the project root (`marksheet-verifier`):

```powershell
# 1) Create a Python virtual environment (local to this project, not global)
python -m venv .venv

# 2) Activate it
.\.venv\Scripts\Activate.ps1
#    If activation is blocked by execution policy, run PowerShell once as:
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3) Upgrade pip and install Python dependencies
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Verify your tools

```powershell
python --version
# Tesseract / ExifTool may not be on PATH; verify via the project checker:
python -c "from backend.app.utils import command_checks as c; import json; print(json.dumps(c.check_all_tools(), indent=2))"
```

If both show `"available": true`, you are ready.

---

## Run the command-line analyzer

**Option A — use the built-in dummy sample (no real data needed):**

```powershell
# Generate a clearly-marked SPECIMEN marksheet image
python sample_data/generate_dummy_marksheet.py

# Analyze it
python backend/analyze.py sample_data/dummy_marksheet.png
```

**Option B — analyze your own file:**

```powershell
python backend/analyze.py uploads/sample.pdf
python backend/analyze.py uploads/sample.jpg
```

You will get:
- a terminal summary (file, OCR confidence, board, risk score, label, flags),
- a JSON report at `reports/<name>_report.json`,
- debug images at `forensic_outputs/<name>__*.png`.

> If you pass a file that does not exist, the analyzer tells you exactly what to
> do instead of crashing.

---

## Current limitations (Phase 1)

- Field detection (roll number, total marks, etc.) is simple regex and will miss
  unusual layouts. It feeds **weak signals** only.
- The risk score is a **transparent heuristic**, not a trained model. It is for
  **prioritisation**, never for automatic rejection.
- Metadata can be misleading: scanning apps, WhatsApp forwarding, and ordinary
  re-saving all change software tags and dates legitimately.
- No real verification against any board / DigiLocker / NAD yet (that needs
  official APIs and is out of scope for the MVP).
- Reviewer decisions in the UI are saved in the browser only (localStorage);
  the backend does not persist them yet.

---

## Production cleanup + deployment preparation (Phase 10)

Phase 10 makes the full stack **production-configurable** without changing how it
runs locally (every new setting has a safe default). **This phase prepares for
deployment; it does not deploy** — that's Phase 11.

**What it adds**
- **Configurable backend** via env vars: `ENVIRONMENT`, `FRONTEND_URL`,
  `BACKEND_URL`, `SETUP_SECRET`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_UPLOAD_EXTENSIONS`
  (plus the existing DB/LLM/JWT vars).
- **Configurable frontend** via `VITE_API_BASE_URL` — no more hardcoded backend
  URL in the React code.
- **Safe CORS:** allowed origins come from `FRONTEND_URL` (comma-separated
  supported). In `production` CORS is restricted to those origins — **never** `*`.
- **Upload validation** on every upload route: extension allow-list, size limit,
  empty-file rejection, filename sanitisation, and **magic-byte content sniffing**
  (a renamed `.exe`/`.zip`/`.html` posing as a PDF/image is rejected).
- **Health check:** `GET /health` now returns `{status, environment, database,
  llm_enabled, version}` (no secrets) for deployment platforms.
- **Deployment-friendly first admin:** `POST /auth/setup-admin` (see below).
- **Global error handling + logging:** generic 500s in production (no
  tracebacks), structured logs that never include passwords, tokens, secrets, or
  document text. Expired tokens (401) auto-log-out the frontend.
- **Storage seam:** `backend/app/services/storage_service.py` centralises file
  storage (local now) with documented TODOs for object storage (S3/R2/Supabase).

### Configuration

Backend — copy `backend/.env.example` to `backend/.env` (all values have local
defaults):

```env
DATABASE_URL=sqlite:///./marksheet_verifier.db
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
LLM_ENABLED=false
LLM_MAX_TOKENS=900
JWT_SECRET_KEY=change_this_to_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
SETUP_SECRET=change_this_to_a_long_random_setup_secret
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://127.0.0.1:8000
ENVIRONMENT=development
MAX_UPLOAD_SIZE_MB=10
ALLOWED_UPLOAD_EXTENSIONS=.pdf,.png,.jpg,.jpeg
```

Frontend — copy `frontend/.env.example` to `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> ⚠️ Only `VITE_`-prefixed variables are exposed to the browser. **Never** put
> API keys or secrets in `frontend/.env` — anything there is public.

### Health check

```powershell
curl.exe http://127.0.0.1:8000/health
# { "status":"ok", "environment":"development", "database":"connected",
#   "llm_enabled":false, "version":"phase-10", ... }
```

### Creating the first admin

- **Local development:** `cd backend && python create_admin.py` (interactive).
- **After deployment** (no shell access): set a strong `SETUP_SECRET`, then call
  the one-time bootstrap endpoint **once**:

```powershell
$body = @{
  email        = "admin@example.com"
  full_name    = "Admin User"
  password     = "StrongPassword123"
  setup_secret = "<your SETUP_SECRET>"
} | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:8000/auth/setup-admin" -Method Post -ContentType "application/json" -Body $body
```

`/auth/setup-admin` is **disabled** unless `SETUP_SECRET` is set, and it refuses
once any admin/reviewer exists ("Admin setup is already completed."). **Never
commit or share `SETUP_SECRET`.**

### Deployment preparation notes

- Local default DB is **SQLite**; switch to **PostgreSQL** for production by
  setting `DATABASE_URL` (install a driver: `pip install "psycopg[binary]"`).
- Local `uploads/` is for development; use object storage in production (see
  `storage_service.py`).
- Set `ENVIRONMENT=production`, a real `FRONTEND_URL`, strong `JWT_SECRET_KEY`
  and `SETUP_SECRET`, and serve over HTTPS.
- Full steps: [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md).

### Security limitations (for now)

- Not yet deployed; no rate limiting, account lockout, refresh tokens, or
  antivirus scanning of uploads.
- Don't expose this publicly with **real** student data until the production
  hardening in the checklist is done. Free-tier **deployment is Phase 11**.

---

## Authentication + role-based access control (Phase 9)

Phase 9 secures the workflow with **email/password login**, **JWT access tokens**,
and **role-based access control**. Passwords are hashed with bcrypt (via passlib);
tokens are signed JWTs (python-jose). Nothing about the AI changes — auth controls
*who can see what*; a human reviewer is still the only thing that decides a case.

**Roles**

| Role | How it's created | Can access |
|------|------------------|-----------|
| `student` | self-registration (`/register`) | submit & track **their own** marksheets; only safe statuses |
| `admin`, `reviewer` | server-side via `create_admin.py` | admin dashboard, case detail + signals, record decisions, audit trail |

**Student vs admin permissions**
- A student only ever sees safe statuses for **their own** submissions. The risk
  score, forensics score, metadata warnings, agent trace, and AI explanation are
  **never** returned to a student.
- Admin/reviewer routes are protected: **no token → 401**, **student token → 403**.
- Public registration always creates a **student** — you cannot self-register as
  admin/reviewer.

**How JWT works here (high level):** you log in with email + password → the
backend verifies the bcrypt hash and returns a signed JWT containing your user id
and role → the frontend stores it (localStorage) and sends it as
`Authorization: Bearer <token>` on every protected request → a FastAPI dependency
decodes the token, loads the active user, and enforces the role. JWTs are
stateless, so **logout** simply discards the token client-side.

**Auth environment variables** (add to `backend/.env`):

```env
JWT_SECRET_KEY=replace_with_a_long_random_secret   # CHANGE for production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

Generate a strong secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

### Create the first admin / reviewer

Admin and reviewer accounts are **not** self-registerable. Create one from the
backend folder (you'll be prompted for email, name, role, and a hidden password —
nothing is hardcoded):

```powershell
cd backend
python create_admin.py
```

### Register / log in as a student

- In the UI: open **Register**, create a student account (auto-logs you in), then
  use **Student Upload** and **Track My Submissions**.
- Or via API:

```powershell
# Register (always creates a student)
$body = @{ email="student@example.com"; full_name="Demo Student"; password="StrongPassword123" } | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:8000/auth/register" -Method Post -ContentType "application/json" -Body $body

# Login -> returns { access_token, token_type, user }
$body = @{ email="student@example.com"; password="StrongPassword123" } | ConvertTo-Json
$login = Invoke-RestMethod "http://127.0.0.1:8000/auth/login" -Method Post -ContentType "application/json" -Body $body
$token = $login.access_token

# Use the token on protected requests
Invoke-RestMethod "http://127.0.0.1:8000/auth/me" -Headers @{ Authorization = "Bearer $token" }
Invoke-RestMethod "http://127.0.0.1:8000/student/my-submissions" -Headers @{ Authorization = "Bearer $token" }
```

### How protected routes work (frontend)

- An `AuthProvider` holds the user + token and restores the session from a stored
  token on load.
- `ProtectedRoute` requires a logged-in user; `RoleProtectedRoute` additionally
  restricts a page to given roles.
- Student pages (Student Upload, Track My Submissions) require a **student** login;
  Admin Dashboard, Case Detail, and Policy Assistant require **admin/reviewer**.
  The navigation only shows links appropriate to your role.

### New auth endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/register` | public | create a student account |
| `POST` | `/auth/login` | public | get a JWT + safe user info |
| `GET`  | `/auth/me` | bearer | current user |
| `POST` | `/auth/logout` | bearer | client discards token |
| `GET`  | `/student/my-submissions` | student | list **your** submissions (safe) |

Phase 8 routes are now protected: `/student/submit` and
`/student/submission/{id}` require a student login (and enforce ownership); all
`/admin/*` routes require admin/reviewer.

### Security limitations for a demo deployment

- **Do not commit `backend/.env`** (it's git-ignored). Set secrets via environment
  variables.
- **`JWT_SECRET_KEY` must be changed** from the dev default for any real use.
- This is a student-grade baseline: **no** refresh-token rotation, rate limiting,
  account lockout, password reset, or MFA. Don't expose it publicly with real
  student data.
- Legacy dev endpoints (`/upload`, `/cases`, `/reports/{id}`,
  `/cases/{id}/agent-trace`) remain **unauthenticated** for backward compatibility
  and expose internal fields — keep them local-only; the student UI never uses them.

---

## Database + student/admin workflow (Phase 8)

Phase 8 turns the project into a small credential-verification platform with a
real **persistence layer** (SQLAlchemy), a separate **student** and **admin**
workflow, and an **audit trail**.

**What the database adds**
- Structured tables: `users`, `cases`, `student_submissions`, `review_decisions`,
  `audit_logs`.
- **SQLite by default** (a single local file, zero setup) and **PostgreSQL-ready**
  via `DATABASE_URL`.
- The DB stores case metadata + **file paths**, not raw bytes. Uploaded files
  (`uploads/`) and JSON reports (`reports/`) are still on disk and **unchanged**.

**Why SQLite locally / Postgres later:** SQLite needs no server and is perfect
for development and demos. To deploy, set
`DATABASE_URL=postgresql+psycopg://user:pass@host:5432/marksheet` and install a
driver — no code changes.

**Student portal** (`/student-upload`, `/track`)
- Students submit a marksheet with their details and receive a **submission ID**.
- They can track a **safe status** only: *submitted / processing / under review /
  verified / re-upload required / official verification required / closed*.
- Students **never** see the risk score, forensics score, metadata warnings,
  agent trace, or AI explanation.

**Admin portal** (`/admin`, case detail)
- The dashboard lists cases from the database with admin fields.
- The case page adds a **reviewer decision panel** (decision + reviewer comment +
  student-facing status), a **decision history**, and an **audit trail** — on top
  of the existing agent trace, forensics, and AI explanation panels.
- The system never auto-decides; recording a decision is a **human action**.

**Audit trail** records: `document_uploaded`, `analysis_started`,
`analysis_completed`, `status_updated`, `review_decision`.

### New endpoints

| Method | Path | Who | Purpose |
|--------|------|-----|---------|
| `POST` | `/student/submit` | student | submit a marksheet (safe response) |
| `GET`  | `/student/submission/{case_id}` | student | track status (safe, no risk) |
| `GET`  | `/admin/cases` | admin | list cases with admin fields |
| `GET`  | `/admin/cases/{case_id}` | admin | full detail (DB + report + history) |
| `POST` | `/admin/cases/{case_id}/decision` | admin | record a human reviewer decision |
| `GET`  | `/admin/cases/{case_id}/audit` | admin | the case audit trail |

All previous endpoints (`/upload`, `/cases`, `/reports/{id}`, `/agent-trace`,
`/rag/*`, `/forensics/*`, `/cases/{id}/explain`) are unchanged.

### Initialize the database

Tables, demo users, and a backfill of existing cases happen automatically on
backend startup. To initialize manually:

```powershell
python -c "import sys; sys.path.insert(0,'backend'); from app.init_db import init_db; init_db()"
```

### Test Phase 8

```powershell
# A) Install requirements (adds sqlalchemy, alembic, passlib, python-jose)
python -m pip install -r backend/requirements.txt

# B) Ensure backend/.env has (DATABASE_URL is optional — defaults to local SQLite):
#    DATABASE_URL=sqlite:///./marksheet_verifier.db
#    ANTHROPIC_MODEL=claude-sonnet-4-6   (a current id; the 3.5 alias is retired)
#    LLM_ENABLED=true                    (optional)

# C) Start the backend from the project root
python -m uvicorn app.main:app --reload --app-dir backend

# D) Track a submission (paste a real case id)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/student/submission/PASTE_CASE_ID"

# E) Admin list
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/cases"

# F) Record a reviewer decision (human action)
$body = @{
  decision = "needs_more_documents"
  reviewer_comment = "OCR confidence is moderate. Please request a clearer copy."
  student_status = "reupload_required"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/cases/PASTE_CASE_ID/decision" -Method POST -ContentType "application/json" -Body $body

# G) Track again -> student now sees "reupload_required" + a safe action message
Invoke-RestMethod -Uri "http://127.0.0.1:8000/student/submission/PASTE_CASE_ID"

# H) Frontend
cd frontend
npm run dev
#   Student Upload -> submit -> copy ID -> Track Submission;
#   Admin Dashboard -> open case -> add decision -> see audit trail.
```

> **Privacy & safety:** uploaded files are stored on disk in local development;
> the database stores case metadata and paths. The DB file and `uploads/`,
> `reports/`, `forensic_outputs/` are git-ignored. **Do not upload real student
> documents to public demos** — use dummy/sample files only. Students see safe
> statuses only, never internal risk details. See
> [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md).

## Optional Claude API mode (Phase 7)

Phase 7 adds an **optional** Claude-powered answer mode on top of the Phase 6
local RAG. It uses Claude to phrase a better, source-grounded answer from the
**same** retrieved policy chunks — it does **not** make decisions.

**The app works in two modes:**
- **Local fallback (default):** no key, or `LLM_ENABLED=false` → the Phase 6
  local template answers (`mode: local_retrieval_template`).
- **Claude RAG:** `LLM_ENABLED=true` **and** a valid `ANTHROPIC_API_KEY` → Claude
  phrases the answer (`mode: claude_rag`). If the call fails for any reason, it
  falls back automatically (`mode: local_retrieval_template_fallback`).

**Why the API key is optional:** everything works without it. Claude is a
convenience layer; the local fallback always remains.

**Security & privacy (important):**
- The key is read **only** from `backend/.env` via `python-dotenv` — never
  hardcoded, never committed, never returned by any endpoint.
- OCR text and the reviewer's question are treated as **untrusted** input; the
  system prompt tells Claude to ignore embedded instructions and forbids
  accusatory wording. Claude **cannot** change the risk score, status, reports,
  or any reviewer decision — it produces an explanation only.

### How to create `backend/.env`

```powershell
# from the project root
Copy-Item backend\.env.example backend\.env
# then edit backend\.env and set:
#   ANTHROPIC_API_KEY=sk-ant-...        (your real key)
#   ANTHROPIC_MODEL=claude-sonnet-4-6   (a CURRENT id; the old 3.5 alias is retired)
#   LLM_ENABLED=true
#   LLM_MAX_TOKENS=900
```

> **Do not commit `backend/.env`.** It is git-ignored. Only `backend/.env.example`
> (which has no secret) is committed.
>
> **Model note:** use a current model id such as `claude-sonnet-4-6` (balanced),
> `claude-haiku-4-5` (cheap/fast), or `claude-opus-4-8` (most capable). The older
> `claude-3-5-sonnet-latest` alias is **retired** and returns a 404 (the app then
> falls back to local answers and reports the error).

### New endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/rag/llm-status` | `{ llm_enabled, api_key_configured, model, mode }` (no key) |
| `POST` | `/cases/{case_id}/explain` | Source-grounded case explanation (Claude or fallback) |

`POST /rag/ask` now also returns `mode`, `model`, `llm_available`, `llm_error`.

### In the UI

- **Policy Assistant** (`/assistant`): a **"Check LLM Status"** button and a status
  chip (Claude RAG · model / Local fallback), plus a **mode badge** on every
  answer.
- **Case Detail**: a **"Generate LLM Explanation"** button that shows the
  explanation, mode badge, sources used, and limitations.

### Test Phase 7

```powershell
# A) Install requirements (adds anthropic + python-dotenv)
python -m pip install -r backend/requirements.txt

# B) Create backend/.env (see above), then start the backend from the project root
python -m uvicorn app.main:app --reload --app-dir backend

# C) LLM status
curl.exe http://127.0.0.1:8000/rag/llm-status

# D) Ask (PowerShell — avoids JSON-escaping pain)
$body = @{ question = "Are pixel forensics proof of tampering?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/rag/ask" -Method POST -ContentType "application/json" -Body $body

# E) Ask about a case (paste a real case id from GET /cases)
$body = @{ question = "Explain this case for a reviewer."; case_id = "PASTE_CASE_ID" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/rag/ask" -Method POST -ContentType "application/json" -Body $body

# F) Generate a case explanation
Invoke-RestMethod -Uri "http://127.0.0.1:8000/cases/PASTE_CASE_ID/explain" -Method POST

# G) Frontend
cd frontend
npm run dev
```

When a valid key + `LLM_ENABLED=true` are set, the answers show **mode: claude_rag**
and the model name; otherwise they show **local fallback**.

> **LLM explanation limitation:** Claude can be imperfect, cannot confirm fraud,
> and never makes the final decision — see
> [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md) →
> *"LLM Explanation Limitations"*.

## RAG policy assistant (Phase 6)

Phase 6 adds a **local Retrieval-Augmented Generation (RAG)** policy assistant.
Reviewers can ask questions like *"Why is this case needs_review?"*, *"What
should I do if metadata shows Photoshop?"*, or *"Are pixel forensics proof?"* and
get answers grounded in the project's own policy documents.

**What "RAG" means here:** the assistant **retrieves** the most relevant passages
from `docs/` and **generates** an answer from them. In this MVP, generation is a
deterministic template that quotes the retrieved policy text (extractive) — there
is **no LLM**.

**Why no API key is required:** retrieval uses a local **TF-IDF** index
(scikit-learn) built from local markdown files; answers are assembled from the
retrieved sentences with templates. No Claude/OpenAI/Gemini/Hugging Face API is
called.

**How local retrieval works:**
1. Read every `.md` file in `docs/`.
2. Split into ~500–1000 character chunks (kept with their headings).
3. Build a TF-IDF matrix in memory; rank chunks by cosine similarity to the question.
4. Return the top chunks; extract the most relevant sentences into a concise answer.
5. If `case_id` is given, prepend a short case summary (risk label/score, OCR
   confidence, metadata flag count, forensics anomaly, human-review recommendation).

**Knowledge documents:** `PROJECT_PLAN.md`, `ETHICS_AND_LIMITATIONS.md`,
`API_REQUIREMENTS.md`, `REVIEWER_GUIDELINES.md`, `RAG_POLICY_KNOWLEDGE.md`.

**Endpoints:** `POST /rag/ask` (optionally case-aware), `GET /rag/sources`,
`POST /rag/reindex` (rebuild the index after editing docs).

**In the UI:** a new **Policy Assistant** page (`/assistant`) with a chat-like
interface, starter-question chips, an optional case dropdown, and the sources +
limitations for every answer. The Case Detail page has an **"Ask Policy Assistant
about this case"** button that opens the assistant pre-scoped to that case.

### Test Phase 6

```powershell
# A) Install/update backend requirements (adds scikit-learn)
python -m pip install -r backend/requirements.txt

# B) Start the backend (from the project root)
python -m uvicorn app.main:app --reload --app-dir backend

# C) List indexed documents
curl.exe http://127.0.0.1:8000/rag/sources

# D) Ask a general policy question
curl.exe -X POST http://127.0.0.1:8000/rag/ask -H "Content-Type: application/json" -d '{"question":"Are pixel forensics proof of tampering?"}'

# E) Ask about a specific case (paste a real case id from GET /cases)
curl.exe -X POST http://127.0.0.1:8000/rag/ask -H "Content-Type: application/json" -d '{"question":"Why is this case marked the way it is?","case_id":"PASTE_CASE_ID"}'

# F) Frontend
cd frontend
npm run dev
#    open http://localhost:5173 -> Policy Assistant
```

> **Limitations of local template answers:** answers quote existing policy text
> rather than reasoning like a human expert, and are only as complete as the
> `docs/`. They are guidance, never a decision. See
> [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md) →
> *"RAG Assistant Limitations"*.
>
> **Future upgrade (optional LLM mode):** a later phase could add an optional
> Claude/OpenAI API key to phrase answers more naturally on top of the same
> retrieved context. The app is designed to work fully **without** any LLM key.

## Agentic orchestration (Phase 5)

Phase 5 reorganises the analysis into a **local, rule-based agentic workflow** —
no LLM, no external AI/API, fully offline. Each agent has one responsibility and
**reuses the existing services**; an Orchestrator runs them in order and writes
an `agentic_workflow` trace into the report.

```
Student Upload -> Orchestrator
                  -> OCR Agent
                  -> Metadata Agent
                  -> Forensics Agent
                  -> Rule Validation Agent
                  -> Decision Agent
                  -> Evidence Report -> Human Review
```

- **OCR Agent** — text, confidence, detected fields (reuses `ocr_service`).
- **Metadata Agent** — ExifTool warning flags (reuses `metadata_service`).
- **Forensics Agent** — Phase 4 anomaly score + visualizations (reuses `forensics_service`).
- **Rule Validation Agent** — deterministic field checks (roll/total/percentage/result/board).
- **Decision Agent** — aggregates evidence, calls `risk_service`, and produces a
  non-accusatory recommendation + `human_review_required` flag.

The Orchestrator assigns a `run_id`, records each agent's status / duration /
findings / warnings, **continues even if a weak agent fails**, and only aborts on
critical input failures (missing file, missing Tesseract, PDF/preprocess error).

**Why no API key is required:** the agents are plain Python rule modules reusing
local tools (Tesseract, ExifTool, OpenCV, Pillow, NumPy, PyMuPDF). No
Claude/OpenAI/Gemini/Hugging Face/DigiLocker API is called. *(Claude Code, used
to build this project, is separate from the project's runtime and needs no
project API key.)*

**New route:** `GET /cases/{case_id}/agent-trace` returns just the
`agentic_workflow` section (or `{ "available": false, ... }` for older reports).

**In the UI:** the Case Detail page shows an **"Agentic Workflow Trace"** panel
with the run ID, mode (`local_rule_based`), duration, agent count, the
human-review recommendation, and a timeline card per agent (status, duration,
findings, warnings, errors). The Admin Dashboard header shows cases needing human
review and the average OCR confidence.

### Test Phase 5

```powershell
# A) Command-line analyzer (now runs the local agent workflow)
python backend/analyze.py uploads/dummy_marksheet.png
python backend/analyze.py uploads/dummy_marksheet_pdf.pdf
#    -> prints each agent (OCR/Metadata/Forensics/Rule Validation/Decision)

# B) Backend + Swagger: upload, then read the agent trace
python -m uvicorn app.main:app --reload --app-dir backend
#    open http://127.0.0.1:8000/docs -> POST /upload -> copy case_id
#    then GET /cases/{case_id}/agent-trace

# C) Frontend: open a case -> "Agentic Workflow Trace"
cd frontend
npm run dev
```

> **Agentic AI limitation:** these agents are local rule-based modules. They
> produce *evidence summaries*, not proof, and never make the final admission
> decision — a human does. See
> [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md) →
> *"Agentic AI Limitations"*.

## Image forensics (Phase 4)

Phase 4 adds **local pixel/image forensics** using only OpenCV, Pillow, NumPy,
and PyMuPDF — no ML models, no GPU, no cloud. Forensics runs automatically as
part of every analysis (CLI and `/upload`) and adds an `image_forensics` block
to the report.

**Signals generated** (all *weak evidence only*):
- **ELA difference** — Error-Level-Analysis-style recompression view
- **Edge density** — Canny edge map (informational context)
- **Sharpness inconsistency** — local sharpness/blur map
- **Noise inconsistency** — local noise residual map
- **Anomaly heatmap** — the weak signals combined and overlaid on the page

**Where outputs are stored:** one folder per case —
`forensic_outputs/<case_id>/` containing `normalized.png`, `ela.png`,
`edge_map.png`, `sharpness_map.png`, `noise_map.png`, `anomaly_heatmap.png`.

**How risk is affected:** a single `anomaly_score` (0–1) is computed and can add
**at most +0.20** to the overall risk score (bands: >0.75 → +0.20, >0.50 →
+0.12, >0.30 → +0.06, else +0.00). Forensics can *nudge* but never *drive* the
score, and OCR/metadata/field checks remain more important. If forensics fails,
the report records `"available": false` and analysis continues normally.

**New backend routes:**
- `GET /forensics/{case_id}` — list the available forensic image URLs for a case.
- `GET /forensic-files/{case_id}/{filename}` — serve one forensic image
  (only `.png/.jpg/.jpeg`, only from inside that case's folder, path-traversal safe).

**In the UI:** the **Case Detail** page shows an *Image Forensics Signals* panel
with the anomaly score, per-signal meters, the six visualizations, and a clear
limitations note. Older reports without forensics degrade gracefully.

> ⚠️ **Pixel forensics are weak signals only.** Compression, scanning, mobile
> capture, screenshots, WhatsApp forwarding, and PDF conversion can all create
> false positives. See [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md)
> → *"Limitations of Pixel-Level Forensics"*. These visualizations are review
> aids and do **not** prove tampering.

### Test Phase 4

```powershell
# A) Command-line analyzer (now also generates image_forensics)
python backend/analyze.py uploads/dummy_marksheet.png
python backend/analyze.py uploads/dummy_marksheet_pdf.pdf
#    -> see "Forensics anomaly" in the summary; images appear in
#       forensic_outputs/<name>/

# B) Backend + Swagger: upload a file, then call the forensics route
python -m uvicorn app.main:app --reload --app-dir backend
#    open http://127.0.0.1:8000/docs  -> POST /upload  -> copy the case_id
#    then GET /forensics/{case_id}

# C) Frontend: open a case and scroll to "Image Forensics Signals"
cd frontend
npm run dev
#    open http://localhost:5173 -> upload -> View full report
```

## Frontend (Phase 3) at a glance

React + Vite + Tailwind CSS v4, with `lucide-react` icons and `motion`
animations. Custom shadcn-style components (no shadcn CLI needed).

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Landing | Hero, feature cards, ethics note |
| `/upload` | Upload | Drag-and-drop upload + animated result card |
| `/admin` | Admin Dashboard | Stat cards + cases table (+ empty/error states) |
| `/cases/:caseId` | Case Detail | Full report, metadata flags, OCR text, reviewer actions |

API calls live in [frontend/src/api.js](frontend/src/api.js):
`uploadFile`, `getCases`, `getReport`, `getHealth`.

## Future improvements (later phases)

- **Phase 4:** Real pixel forensics (ELA, noise/edge/blur inconsistency, heatmaps).
- **Phase 5:** Local rule-based **agent** orchestration (Metadata/OCR/Forensics/Decision agents) — no external AI API.
- **Phase 6:** `/metrics` endpoint for Prometheus.
- **Phase 7:** Docker + Prometheus + Grafana wiring.

---

## Privacy & ethics (read this)

- **Never commit real student marksheets.** `uploads/`, `reports/`, and
  `forensic_outputs/` are git-ignored. Use the dummy generator for demos.
- The system produces **risk signals only**. No automatic accusation or rejection.
- A **human reviewer** is required for every flagged case.
- Do not store API keys in code; there is **no** real API integration in the MVP.

Full ethics notes live in `docs/ETHICS_AND_LIMITATIONS.md` (added with the docs phase).
