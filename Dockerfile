# Dockerfile for RAG Study Chatbot
# Multi-stage not needed; image is small enough and we want the model cache
# to survive container restarts when a volume is mounted.

FROM python:3.11-slim

# ---- System deps for pdfplumber / pypdf / docx ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2 \
    libxslt1.1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code + static + bundled notes
COPY app/        ./app/
COPY static/     ./static/
COPY pdf/        ./pdf/
COPY data/       ./data/

# Pre-download the embeddings model at build time so the first boot is fast
# and works even offline. Comment out if it makes your build too slow.
RUN python -c "from app.rag.embeddings import get_embeddings; get_embeddings()" || echo "model prefetch skipped"

EXPOSE 8000

# uvicorn with a single worker (the model is heavy; scale horizontally instead)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
