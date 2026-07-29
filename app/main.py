"""
Application entrypoint.

Run locally with:
    uv run uvicorn app.main:app --reload

In production (Render / Docker):
    uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

import asyncio
import os
import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

app = FastAPI(
    title="RAG Study Chatbot",
    description=(
        "A retrieval-augmented study assistant that answers *strictly* from your "
        "uploaded notes (PDF / DOCX / MD / TXT). Built with LangChain, LangGraph, "
        "sentence-transformers and Chroma."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ---- CORS ---------------------------------------------------------------
# Allow the configured origins (defaults to localhost). On cloud platforms we
# auto-detect the service URL so the frontend can call the API.
try:
    origins = settings.cors_origins_list()
except Exception:
    origins = ["*"]

external_url = (
    os.getenv("RENDER_EXTERNAL_URL")
    or os.getenv("SNAPDEPLOY_APP_URL")
    or os.getenv("KOYEB_APP_URL")
    or os.getenv("RAILWAY_PUBLIC_DOMAIN")
)
if external_url:
    origins.append(external_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Root-level routes (MUST be before static mount) --------------------
@app.get("/health")
async def health_root():
    """Root-level health check required by SnapDeploy."""
    return {"status": "ok"}

@app.get("/api")
async def api_root():
    """Tiny landing for the API namespace."""
    return {
        "name": "RAG Study Chatbot API",
        "docs": "/api/docs",
        "endpoints": [r.path for r in app.routes],
    }

# ---- API routes ---------------------------------------------------------
app.include_router(api_router)


# ---- Startup: warm up + auto-ingest ------------------------------------
@app.on_event("startup")
async def _on_startup():
    """
    On boot we:
      1. Pre-load the embeddings model so the first question is fast.
      2. If the vector DB is empty AND we have bundled notes, ingest them.
         This is what makes the app survive Render's ephemeral filesystem:
         the default knowledge base is always rebuilt on cold starts.
    """
    log.info("Starting RAG Study Chatbot...")

    # 1) warm up embeddings in a background thread (don't block startup)
    def _warm():
        try:
            from app.rag.embeddings import get_embeddings

            get_embeddings()
            log.info("Embeddings model pre-loaded")
        except Exception as e:  # noqa: BLE001
            log.error(f"Could not pre-load embeddings: {e}")

    asyncio.get_event_loop().run_in_executor(None, _warm)

    # 2) auto-ingest bundled notes if store is empty
    try:
        from app.rag.ingest import ingest_notes_directory
        from app.rag.vectorstore import collection_count

        if collection_count() == 0:
            log.info("Vector store empty — ingesting bundled notes/")
            added = ingest_notes_directory()
            log.info(f"Auto-ingested {added} chunk(s) on startup")
        else:
            log.info("Vector store already populated — skipping auto-ingest")
    except Exception as e:  # noqa: BLE001
        log.error(f"Startup ingestion failed: {e}")

    # 3) optional keep-alive (anti-sleep for free-tier cloud)
    if settings.keep_alive_enabled and (settings.keep_alive_url or external_url):
        from app.core.keepalive import start_keep_alive

        start_keep_alive(settings.keep_alive_url or external_url)


# ---- Static frontend (served at /) - MUST be LAST to avoid shadowing routes
_static_dir = settings.resolve("static")
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
else:
    log.warning("static/ directory missing — frontend will not be served")
