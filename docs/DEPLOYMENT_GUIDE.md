# Deployment Guide (Phase 11) — Free-Tier Deployment

A beginner-friendly, step-by-step guide (written for Windows / PowerShell) to
deploy **marksheet-verifier** on free-tier platforms:

| Layer | Platform (free tier) |
|-------|----------------------|
| Frontend (React/Vite) | **Vercel** |
| Backend (FastAPI) | **Render** |
| Database (PostgreSQL) | **Supabase** *or* **Neon** |
| File storage | local disk for the first test (see limitations) |
| Claude (optional) | Anthropic API key via backend env var |

> **This guide prepares and explains deployment. It does not deploy for you.**
> You run the steps manually. Nothing here contains real secrets — you paste
> your own values into each platform's dashboard.

> The config files referenced here already exist in the repo:
> [`render.yaml`](../render.yaml), [`backend/runtime.txt`](../backend/runtime.txt),
> [`backend/Dockerfile`](../backend/Dockerfile) (optional),
> [`frontend/vercel.json`](../frontend/vercel.json),
> [`backend/.env.example`](../backend/.env.example),
> [`frontend/.env.example`](../frontend/.env.example).

---

## A. Pre-deployment checklist (do this first, locally)

- [ ] Phase 10 tests pass locally.
- [ ] Latest code is pushed to GitHub.
- [ ] `backend/.env` is **not** committed (only `backend/.env.example`).
- [ ] `frontend/.env` is **not** committed (only `frontend/.env.example`).
- [ ] The database file (`*.db`) is **not** committed.
- [ ] `uploads/`, `reports/`, `forensic_outputs/` are **not** committed.
- [ ] `/health` works locally.
- [ ] `npm run build` works locally.

Quick local verification:

```powershell
cd C:\Users\purva\Downloads\marksheet-verifier
git status                      # confirm no .env / *.db / uploads in the list

# backend health
cd backend
python -m uvicorn app.main:app --reload
# in another terminal:
curl.exe http://127.0.0.1:8000/health

# frontend build
cd ..\frontend
npm run build
```

---

## B. Create a PostgreSQL database

Pick **one** provider. Both are free and work the same way — you just need the
connection string.

### Option 1 — Supabase

1. Create a project at <https://supabase.com>.
2. Go to **Project Settings → Database → Connection string → URI**.
3. Copy the URI. It looks like:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`
4. Replace `[YOUR-PASSWORD]` with your database password.

### Option 2 — Neon

1. Create a project at <https://neon.tech>.
2. Copy the connection string from the dashboard. It looks like:
   `postgresql://user:password@ep-xxxx.region.aws.neon.tech/dbname?sslmode=require`

### Notes for both

- You will paste this as **`DATABASE_URL`** in Render (step C). **Do not commit it.**
- If your URL starts with `postgres://`, that's fine — the backend automatically
  rewrites it to `postgresql://` (which SQLAlchemy requires).
- If the connection is rejected for SSL, append `?sslmode=require` to the URL.
- The app creates its tables automatically on startup — no manual migration.

---

## C. Deploy the backend on Render

You can deploy via the included **Blueprint** (`render.yaml`) or manually. Manual
is the most beginner-proof:

1. Go to <https://render.com> → **New → Web Service** → connect your GitHub repo.
2. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
   - **Instance Type:** Free
3. Add **Environment Variables** (Render dashboard → *Environment*):

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | *(your Supabase/Neon URL from step B)* |
   | `ANTHROPIC_API_KEY` | *(your Anthropic key, or leave unset)* |
   | `ANTHROPIC_MODEL` | `claude-sonnet-4-6` |
   | `LLM_ENABLED` | `true` *(or `false` to stay in local fallback)* |
   | `LLM_MAX_TOKENS` | `900` |
   | `JWT_SECRET_KEY` | *(a long random string — see below)* |
   | `JWT_ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` |
   | `SETUP_SECRET` | *(a long random string — see below)* |
   | `FRONTEND_URL` | `https://your-vercel-app.vercel.app` *(set in step G)* |
   | `BACKEND_URL` | `https://your-render-backend.onrender.com` |
   | `ENVIRONMENT` | `production` |
   | `MAX_UPLOAD_SIZE_MB` | `10` |
   | `ALLOWED_UPLOAD_EXTENSIONS` | `.pdf,.png,.jpg,.jpeg` |

   Generate strong secrets locally and paste them:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"   # JWT_SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(48))"   # SETUP_SECRET
   ```

   > If you deploy via the Blueprint (`render.yaml`) instead, Render
   > **auto-generates** `JWT_SECRET_KEY` and `SETUP_SECRET` for you — read
   > `SETUP_SECRET` from the dashboard when you need it in step E.

4. Click **Create Web Service** and wait for the build to finish.

> ⚠️ **Tesseract / ExifTool / OpenCV (read this).** Render's native Python
> runtime cannot install system packages (`apt`). The analyzer needs **Tesseract
> OCR** and **ExifTool**, and OpenCV needs **libGL**. The API, auth, database,
> and the RAG/Claude assistant will work on native Python, but **OCR and image
> forensics may fail** there. If they do, use the **Docker fallback (Phase 11B)**
> at the end of this guide.

---

## D. Test the deployed backend

- Open `https://YOUR_BACKEND_URL/health` — you should see
  `{"status":"ok","environment":"production","database":"connected","version":"phase-10",...}`.
- Open `https://YOUR_BACKEND_URL/docs` for the interactive API.
- Check **Logs** in the Render dashboard for the startup line and any errors.

If `database` shows `"error"`, re-check `DATABASE_URL` (password, `sslmode`).

---

## E. Create the first admin (one time)

Admin/reviewer accounts are not self-registerable. After the backend is live,
create the first admin **once** using the protected setup endpoint and your
`SETUP_SECRET`:

```powershell
$body = @{
  email        = "admin@example.com"
  full_name    = "Admin User"
  password     = "StrongPassword123"
  setup_secret = "PASTE_SETUP_SECRET_HERE"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://YOUR_BACKEND_URL/auth/setup-admin" -Method POST -ContentType "application/json" -Body $body
```

- Works only while no admin/reviewer exists yet; afterwards it returns
  *"Admin setup is already completed."*
- After creating the admin you may rotate/remove `SETUP_SECRET` in Render.

---

## F. Deploy the frontend on Vercel

1. Go to <https://vercel.com> → **Add New → Project** → import your GitHub repo.
2. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (auto-detected)
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - (`frontend/vercel.json` already adds the SPA fallback so React Router routes
     like `/admin` don't 404 on refresh.)
3. Add **Environment Variable**:
   - `VITE_API_BASE_URL` = `https://YOUR_BACKEND_URL` (your Render URL)
   > Vite bakes this in at **build time**, so if you change it later you must
   > **redeploy** the frontend.
4. Click **Deploy** and note the resulting URL, e.g. `https://your-app.vercel.app`.

---

## G. Point the backend at the frontend (CORS)

The backend only accepts browser requests from `FRONTEND_URL` in production.

1. In Render → your service → **Environment**, set:
   - `FRONTEND_URL` = `https://your-app.vercel.app` (the Vercel URL from step F)
   - (You can list several comma-separated, e.g. a preview + production URL.)
2. **Save** — Render restarts the backend automatically.

---

## H. Final end-to-end tests (on the deployed app)

Open your Vercel URL and verify:

- [ ] Register a student → login.
- [ ] Upload an allowed file (PDF/PNG/JPG) → submission succeeds.
- [ ] Track the submission (safe status only, no internal risk details).
- [ ] An invalid upload (e.g. `.exe`, or a renamed file) is **rejected**.
- [ ] Login as the admin (from step E) → Admin Dashboard loads.
- [ ] Open a case → generate the Claude explanation (or local fallback).
- [ ] Add a review decision → student-facing status updates.
- [ ] Confirm the audit trail shows the decision.
- [ ] Logout → protected pages redirect to login.

---

## I. Important limitations (free tier)

- **Cold starts:** the free Render backend **sleeps** when idle; the first
  request after a nap can take ~30–60s. The frontend may show "Cannot reach the
  server" briefly — retry.
- **Slow CPU:** OCR and image forensics are CPU-heavy; they can be slow on small
  free instances.
- **File persistence:** Render's local disk is **ephemeral** — files in
  `uploads/`, `reports/`, and `forensic_outputs/` are **lost on every redeploy/
  restart**. The database rows survive (they're in PostgreSQL), but the original
  files and forensic images may disappear. This is acceptable for a demo.
- **For stronger production:** move file storage to **object storage**
  (Supabase Storage / AWS S3 / Cloudflare R2) and store the object URL in
  `Case.file_path`. The swap point is
  [`backend/app/services/storage_service.py`](../backend/app/services/storage_service.py).
- **System tools:** if OCR/forensics fail on native Render, use the Docker
  fallback below.

---

## Phase 11B — Optional Docker fallback (only if native Render fails OCR)

If the native Python runtime can't run Tesseract/ExifTool/OpenCV, deploy the
backend as a Docker container instead. The repo includes a ready-to-use
[`backend/Dockerfile`](../backend/Dockerfile) that installs Tesseract, ExifTool,
and the OpenCV system libraries.

On Render, create the Web Service with:

- **Runtime:** Docker
- **Dockerfile Path:** `./backend/Dockerfile`
- **Docker Build Context Directory:** `.` (the **repo root** — the image needs
  `docs/` for the RAG assistant)
- Same environment variables as step C.
- Health check path: `/health`.

Test the image locally first (Docker Desktop required):

```powershell
cd C:\Users\purva\Downloads\marksheet-verifier
docker build -t marksheet-backend -f backend/Dockerfile .
docker run -p 8000:8000 -e ENVIRONMENT=development marksheet-backend
curl.exe http://127.0.0.1:8000/health
```

> Docker is **optional** and only needed if the native runtime can't provide the
> OCR/forensics system tools. Everything else (auth, DB, RAG, Claude) works on
> the native Python runtime.

---

**Status:** Phase 11 provides the deployment *files and instructions*. Performing
the deployment (and pasting real secrets into Render/Vercel) is a manual step you
do yourself. See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for the tick-list.
