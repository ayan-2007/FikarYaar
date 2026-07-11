"""
API routes.

Endpoints
---------
GET  /api/health            -> service + knowledge-base health
POST /api/chat              -> one-shot Q&A (JSON in, JSON out)
POST /api/chat/stream       -> SSE streaming Q&A (token-by-token feel)
POST /api/upload            -> upload notes (PDF/DOCX/MD/TXT) and ingest them
POST /api/ingest            -> re-ingest the bundled notes/ folder
GET  /api/sources           -> list the files currently in the knowledge base
DELETE /api/sources/{name}  -> remove a source file + its chunks
"""
from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app import __version__
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestResponse,
    SourceInfo,
    UploadResponse,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    assert_file_size_ok,
    assert_magic_bytes,
    assert_upload_safe,
    safe_filename,
)
from app.rag.graph import ask, format_history
from app.rag.ingest import ingest_documents
from app.rag.llm import has_api_key
from app.rag.loader import load_single_file
from app.rag.vectorstore import (
    collection_count,
    delete_by_source,
    list_sources,
)

log = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["study-bot"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def health():
    """Lightweight readiness check for Render and the frontend."""
    embeddings_loaded = False
    try:
        from app.rag.embeddings import get_embeddings

        # Don't force-load on health check; just probe the cache.
        embeddings_loaded = get_embeddings.__wrapped__.__doc__ is not None  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        embeddings_loaded = False

    sources = list_sources()
    return HealthResponse(
        status="ok",
        version=__version__,
        chunks=collection_count(),
        sources=len(sources),
        llm_configured=has_api_key(),
        embeddings_loaded=embeddings_loaded,
    )


# ---------------------------------------------------------------------------
# Chat (one-shot)
# ---------------------------------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Run the full RAG graph and return the answer + sources."""
    history = [{"role": m.role, "content": m.content} for m in req.history]
    result = ask(req.question, history)
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=[SourceInfo(**s) for s in result.get("sources", [])],
        used_notes=bool(result.get("used_notes", False)),
    )


# ---------------------------------------------------------------------------
# Chat (SSE streaming)
# ---------------------------------------------------------------------------
async def _stream_answer(question: str, history: list[dict]):
    """
    Stream the answer as Server-Sent Events.

    We run the (CPU/IO-bound) graph in a thread so it doesn't block the event
    loop, then we 'fake' a token-by-token stream by emitting the answer in
    small chunks. This gives a great UX without depending on a streaming LLM
    endpoint (Groq streaming differs between SDK versions).
    """
    # 1) thinking indicator
    yield "event: status\ndata: " + json.dumps({"step": "thinking"}) + "\n\n"
    await asyncio.sleep(0)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ask, question, history)

    # 2) send sources first so the UI can render them above the answer
    sources = result.get("sources", [])
    yield "event: sources\ndata: " + json.dumps({"sources": sources}) + "\n\n"

    # 3) stream the answer in ~6-word chunks for a typewriter effect
    answer = result.get("answer", "")
    words = answer.split(" ")
    chunk_size = 4
    buf = []
    for i, w in enumerate(words):
        buf.append(w)
        if len(buf) >= chunk_size or i == len(words) - 1:
            token = " ".join(buf) + " "
            buf = []
            yield "event: token\ndata: " + json.dumps({"token": token}) + "\n\n"
            await asyncio.sleep(0.02)  # smooth cadence

    # 4) done
    yield (
        "event: done\ndata: "
        + json.dumps({"used_notes": bool(result.get("used_notes", False))})
        + "\n\n"
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    return StreamingResponse(
        _stream_answer(req.question, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (Render/nginx)
        },
    )


# ---------------------------------------------------------------------------
# Upload notes
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=UploadResponse)
async def upload_notes(files: List[UploadFile] = File(...)):
    """
    Accept one or more notes files, validate them, save to data/uploads/, and
    ingest them into the vector store immediately.
    """
    assert_upload_safe(files)

    upload_dir = settings.uploads_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    total_chunks = 0

    for f in files:
        raw = await f.read()
        await assert_file_size_ok(raw)

        ext = Path(f.filename or "").suffix.lower()
        assert_magic_bytes(ext, raw[:8])

        fname = safe_filename(f.filename or "note")
        dest = upload_dir / fname
        dest.write_bytes(raw)

        try:
            docs = load_single_file(dest)
            # Use the *original* short name for display, not the timestamped one.
            display = Path(f.filename or "note").name
            for d in docs:
                d.metadata["source_name"] = display
            total_chunks += ingest_documents(docs, source_name=display)
            saved.append(display)
            log.info(f"Uploaded + ingested {display} ({len(raw)} bytes)")
        except Exception as e:  # noqa: BLE001
            log.error(f"Failed to ingest {fname}: {e}")
            # remove the broken file so it doesn't get re-ingested later
            dest.unlink(missing_ok=True)

    return UploadResponse(
        status="ok" if saved else "error",
        files=saved,
        chunks_added=total_chunks,
    )


# ---------------------------------------------------------------------------
# Ingest bundled notes
# ---------------------------------------------------------------------------
@router.post("/ingest", response_model=IngestResponse)
async def ingest_bundled():
    """Re-read and ingest every file in the notes/ folder."""
    from app.rag.loader import load_directory

    notes = load_directory(settings.notes_path)
    files = {d.metadata.get("source_name") for d in notes if d.metadata.get("source_name")}
    chunks = ingest_documents(notes) if notes else 0
    return IngestResponse(
        status="ok",
        files_processed=len(files),
        chunks_added=chunks,
    )


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
@router.get("/sources")
async def get_sources():
    return {"sources": list_sources(), "total_chunks": collection_count()}


@router.delete("/sources/{name}")
async def remove_source(name: str):
    """Remove a source's chunks from the store and delete the uploaded file."""
    delete_by_source(name)
    # Also remove from uploads dir if present
    for p in settings.uploads_path.glob("*"):
        if p.name.endswith(name) or name in p.name:
            p.unlink(missing_ok=True)
    return {"status": "deleted", "name": name}


@router.delete("/sources")
async def wipe_all():
    """Wipe the entire knowledge base (used by the UI's 'reset' button)."""
    from app.rag.vectorstore import reset_vectorstore

    try:
        shutil.rmtree(settings.chroma_path, ignore_errors=True)
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        reset_vectorstore()
        log.info("Knowledge base wiped")
        return {"status": "wiped"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}
