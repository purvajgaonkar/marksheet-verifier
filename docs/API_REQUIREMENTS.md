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
an answer, the source chunks used, a `mode`, and a list of limitations.

---

## Phase 7 Claude API Requirements

Phase 7 adds an **optional** Claude-powered answer mode on top of the same local
retrieval. The app still runs fully without it.

- **`ANTHROPIC_API_KEY` is OPTIONAL for the local fallback, but REQUIRED for the
  Claude-powered mode.** With no key (or `LLM_ENABLED=false`), the assistant uses
  the Phase 6 local template answers (`mode: local_retrieval_template`).
- **The API key must be stored in `backend/.env`** (loaded with `python-dotenv`).
  Copy `backend/.env.example` to `backend/.env` and fill it in.
- **Never hardcode or commit keys.** `backend/.env` is git-ignored; only
  `backend/.env.example` (which has no secret) is committed. The key is read from
  the environment and is never returned by any endpoint.
- **Claude is used for EXPLANATION only, not decisions.** It rephrases answers
  from the retrieved policy context; it cannot change the risk score, status,
  reports, or any reviewer decision.

### Environment variables (`backend/.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | _(empty)_ | Your Anthropic key. Empty = local fallback. |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model id. Use a **current** id (e.g. `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-opus-4-8`). The old `claude-3-5-sonnet-latest` is retired and returns 404. |
| `LLM_ENABLED` | `false` | Master switch. `true` + a valid key enables Claude mode. |
| `LLM_MAX_TOKENS` | `900` | Max tokens Claude may generate per answer. |

### Phase 7 endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/rag/llm-status` | Report `{ llm_enabled, api_key_configured, model, mode }` (no key exposed) |
| `POST` | `/cases/{case_id}/explain` | Source-grounded explanation of a case (Claude or local fallback) |

`POST /rag/ask` now also returns `mode` (`claude_rag` / `local_retrieval_template`
/ `local_retrieval_template_fallback`), `model`, `llm_available`, and `llm_error`.

**Fallback behaviour:** if `LLM_ENABLED=true` but the Claude call fails (bad key,
no credits, wrong model, network error), the request does **not** fail — it falls
back to the local answer with `mode: local_retrieval_template_fallback` and an
`llm_error` describing the problem.

---

## Phase 8 Database Requirements

Phase 8 adds a real persistence layer with **SQLAlchemy**. No external database
service is required for local development.

- **`DATABASE_URL`** controls the connection. Set it in `backend/.env`.
- **SQLite is the local default** — zero setup, a single file
  (`marksheet_verifier.db`). Default value:
  `DATABASE_URL=sqlite:///./marksheet_verifier.db`.
- **PostgreSQL deployment-ready:** point `DATABASE_URL` at a Postgres instance
  and install a driver — nothing else changes. Example:
  `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/marksheet`
  (`pip install "psycopg[binary]"`).
- **Files stay on disk.** The database stores case metadata and file **paths**,
  not raw PDF/image bytes. Uploaded files (`uploads/`) and JSON reports
  (`reports/`) are unchanged.
- **No DB secrets in code.** `DATABASE_URL` is read from the environment;
  `backend/.env` is git-ignored.

### Initialize the database

Tables are created automatically on FastAPI startup (and demo users + existing
cases are backfilled). To initialize manually:

```powershell
python -c "import sys; sys.path.insert(0,'backend'); from app.init_db import init_db; init_db()"
```

---

## Phase 9 Authentication Requirements

Phase 9 adds email/password authentication with **JWT access tokens** and
role-based access control. New environment variables (add to `backend/.env`):

| Variable | Default (dev) | Purpose |
|----------|---------------|---------|
| `JWT_SECRET_KEY` | `dev-insecure-change-me` | Secret used to sign/verify JWTs. **Change for production.** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Access-token lifetime in minutes. |

```env
JWT_SECRET_KEY=change_this_to_a_strong_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

Generate a strong secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Python packages** (already in `backend/requirements.txt`):
`passlib[bcrypt]`, `bcrypt<4.1` (passlib 1.7.4 is incompatible with bcrypt ≥ 4.1),
`python-jose[cryptography]`, `email-validator`.

### Roles & protected endpoints

| Role | Can access |
|------|-----------|
| `student` | `/auth/*`, `/student/submit`, `/student/my-submissions`, `/student/submission/{id}` (own cases only) |
| `admin`, `reviewer` | all admin routes: `/admin/cases`, `/admin/cases/{id}`, `/admin/cases/{id}/decision`, `/admin/cases/{id}/audit` |

Public registration (`POST /auth/register`) **always** creates a `student`.
Admin/reviewer accounts are created server-side with `backend/create_admin.py`.

### Auth endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/auth/register` | public | create a student account |
| `POST` | `/auth/login` | public | get a JWT + safe user info |
| `GET`  | `/auth/me` | bearer token | current user |
| `POST` | `/auth/logout` | bearer token | client discards token (stateless) |

Send the token as `Authorization: Bearer <token>` on protected requests. JWTs are
stateless: "logout" simply discards the token client-side.

> Still **not** needed: no external auth provider, OAuth, SSO, email/SMS, or
> third-party identity service. Authentication is local username/password + JWT.

---

## Phase 10 Deployment Configuration

Phase 10 adds production-configuration variables. All have safe local defaults,
so development still needs zero setup.

### Backend (`backend/.env`)

| Variable | Default (dev) | Purpose |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | `development` = permissive local CORS + error details; `production` = strict CORS + generic errors. |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed browser origin(s) for CORS. Comma-separated for multiple, e.g. `http://localhost:5173,https://your-app.vercel.app`. |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Public URL of the backend (for docs/links). |
| `SETUP_SECRET` | *(empty)* | Enables one-time `POST /auth/setup-admin`. Empty/placeholder = endpoint disabled. **Never commit.** |
| `MAX_UPLOAD_SIZE_MB` | `10` | Maximum accepted upload size, in MB. |
| `ALLOWED_UPLOAD_EXTENSIONS` | `.pdf,.png,.jpg,.jpeg` | Comma-separated allowed file extensions. |

### Frontend (`frontend/.env`)

| Variable | Default (dev) | Purpose |
|----------|---------------|---------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Base URL of the backend API. Only `VITE_`-prefixed vars reach the browser — **never** put secrets here. |

### Health & first-admin endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET`  | `/health` | public | liveness: `{status, environment, database, llm_enabled, version, …}` (no secrets) |
| `POST` | `/auth/setup-admin` | `setup_secret` in body | create the FIRST admin once after deploy (disabled unless `SETUP_SECRET` set; refuses if staff already exist) |

> Still **not** needed: no Docker, Kubernetes, Prometheus, Grafana, MCP, cloud
> storage, or external verification API to run or prepare the app. Object storage
> and PostgreSQL are *recommended for production* but optional and not wired in yet.
