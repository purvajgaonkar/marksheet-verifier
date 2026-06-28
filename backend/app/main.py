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

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config
from app.init_db import init_db

# ---------------------------------------------------------------------------
# Logging (Phase 10). Basic, structured-enough logging. We deliberately never
# log passwords, JWTs, API keys, setup secrets, or full document/OCR text.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("marksheet")
from app.routes import (
    admin_routes,
    auth_routes,
    case_routes,
    forensic_routes,
    health_routes,
    rag_routes,
    student_routes,
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
    version="0.10.0",  # Phase 10
)

# ---------------------------------------------------------------------------
# CORS: only the configured frontend origin(s) may call this API from a browser.
# Origins come from FRONTEND_URL via config; never a wildcard in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handlers (Phase 10).
# In production we return safe, generic messages and never leak tracebacks.
# In development we include the error detail to aid debugging.
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request.", "errors": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def _http_handler(request: Request, exc: StarletteHTTPException):
    # Pass through intended HTTP errors (401/403/404/…) with their detail.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def _unhandled_handler(request: Request, exc: Exception):
    # Log the full error server-side; return a safe message to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    detail = (
        "Internal server error."
        if config.IS_PRODUCTION
        else f"Internal server error: {exc}"
    )
    return JSONResponse(status_code=500, content={"detail": detail})


# ---------------------------------------------------------------------------
# Make sure uploads/, reports/, forensic_outputs/ exist before serving.
# ---------------------------------------------------------------------------
@app.on_event("startup")
def _on_startup() -> None:
    config.ensure_directories()
    # Phase 8: create tables, seed demo users, and backfill existing cases.
    init_db()
    logger.info(
        "Marksheet Verifier API started: environment=%s llm_enabled=%s db=%s",
        config.ENVIRONMENT,
        config.llm_is_available(),
        config.DATABASE_URL.split("://", 1)[0],  # scheme only, never credentials
    )


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
app.include_router(auth_routes.router)
app.include_router(student_routes.router)
app.include_router(admin_routes.router)
