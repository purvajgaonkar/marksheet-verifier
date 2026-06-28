"""
main.py
=======

The FastAPI application for the marksheet verifier (Phase 2).

It wires everything together:
    * enables CORS so the React frontend (Vite :5173 / CRA :3000) can call it,
    * makes sure the working folders exist on startup,
    * mounts the route modules (health, upload, cases/reports),
    * exposes a friendly GET / landing message.

Run it (from the project ROOT, with the venv active):

    python -m uvicorn app.main:app --reload --app-dir backend

Then open the interactive docs at:  http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routes import (
    case_routes,
    forensic_routes,
    health_routes,
    rag_routes,
    upload_routes,
)
from app.schemas import RootResponse
from app.services.report_service import MVP_DISCLAIMER

# ---------------------------------------------------------------------------
# Create the app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Marksheet Verifier API",
    description=(
        "Agentic-AI-inspired marksheet verification and tampering-signal "
        "detection (MVP). Produces evidence-based RISK SIGNALS only — it never "
        "automatically accuses or rejects a student, and a human reviewer makes "
        "the final decision."
    ),
    version="0.2.0",  # Phase 2
)

# ---------------------------------------------------------------------------
# CORS: allow the React dev servers to call this API from the browser.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Make sure uploads/, reports/, forensic_outputs/ exist before serving.
# ---------------------------------------------------------------------------
@app.on_event("startup")
def _on_startup() -> None:
    config.ensure_directories()


# ---------------------------------------------------------------------------
# Landing route
# ---------------------------------------------------------------------------
@app.get("/", response_model=RootResponse, tags=["root"])
def root() -> RootResponse:
    """Basic API message + a pointer to the interactive docs."""
    return RootResponse(
        name="Marksheet Verifier API",
        message=(
            "Welcome. POST a marksheet to /upload, browse cases at /cases, and "
            "read full reports at /reports/{case_id}. See /docs for an "
            "interactive UI."
        ),
        docs_url="/docs",
        disclaimer=MVP_DISCLAIMER,
    )


# ---------------------------------------------------------------------------
# Mount the route modules
# ---------------------------------------------------------------------------
app.include_router(health_routes.router)
app.include_router(upload_routes.router)
app.include_router(case_routes.router)
app.include_router(forensic_routes.router)
app.include_router(rag_routes.router)
