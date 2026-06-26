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

## Project status: Phases 1–3 complete (CLI + API + React UI)

The project is built in phases. **Phase 1** is the offline command-line
analyzer, **Phase 2** wraps the same pipeline in a FastAPI backend, and
**Phase 3** adds a polished React + Vite dashboard. Later phases add deeper
pixel forensics, an agent-style orchestrator, and metrics.

```
                 Phase 1: CLI analyzer            ✅
                 Phase 2: FastAPI backend         ✅
You are here ──► Phase 3: React frontend (Vite)   ✅
                 Phase 4: Pixel/image forensics
                 Phase 5: Agentic orchestration (local rules, no external AI)
                 Phase 6: /metrics endpoint for Prometheus/Grafana
                 Phase 7: Docker + Prometheus
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
