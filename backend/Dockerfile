# =====================================================================
# backend/Dockerfile  -  OPTIONAL Phase 11B deployment fallback
# =====================================================================
# Use this ONLY if Render's native Python runtime cannot provide the system
# tools the analyzer needs (Tesseract OCR + ExifTool, plus the shared libraries
# OpenCV requires). The native runtime (render.yaml) is the default; switch to
# this Docker image if OCR/forensics fail there. See docs/DEPLOYMENT_GUIDE.md.
#
# IMPORTANT: build with the REPO ROOT as the context (not backend/), because the
# RAG policy assistant reads from ../docs. On Render set:
#     Runtime = Docker
#     Dockerfile Path = ./backend/Dockerfile
#     Docker Build Context Directory = .   (the repo root)
# ---------------------------------------------------------------------

FROM python:3.11-slim

# System tools: Tesseract OCR, ExifTool, and the libs OpenCV/PyMuPDF need.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libtesseract-dev \
        libimage-exiftool-perl \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Mirror the repo layout so config.py's PROJECT_ROOT logic and the docs/ folder
# (RAG source) resolve exactly as they do locally.
WORKDIR /repo

# Install Python deps first for better layer caching.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Application code + the policy documents the assistant retrieves from.
COPY backend/ backend/
COPY docs/ docs/

# Render injects $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir backend"]
