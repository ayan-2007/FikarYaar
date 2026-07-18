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
    QuizStartRequest,
    QuizAnswerRequest,
    ResearchRequest,
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
    result = await ask(req.question, history)
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=[SourceInfo(**s) for s in result.get("sources", [])],
        used_notes=bool(result.get("used_notes", False)),
    )



# ---------------------------------------------------------------------------
# Chat (SSE streaming)
# ---------------------------------------------------------------------------
async def _stream_ustad(question: str, history: list[dict]):

    """
    Stream the Ustad answer as Server-Sent Events.
    """
    yield "event: status\ndata: " + json.dumps({"step": "thinking"}) + "\n\n"
    await asyncio.sleep(0)

    result = await ask(question, history)

    sources = result.get("sources", [])
    yield "event: sources\ndata: " + json.dumps({"sources": sources}) + "\n\n"

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
            await asyncio.sleep(0.02)

    yield (
        "event: done\ndata: "
        + json.dumps({"used_notes": bool(result.get("used_notes", False))})
        + "\n\n"
    )


async def _stream_muhaqqiq(question: str, mode: str, source_filter: str | None):
    """
    Run Muhaqqiq in the requested mode and emit a single structured SSE event.
    """
    from app.rag.vectorstore import retrieve_with_threshold, get_vectorstore
    from app.agents.muhaqqiq import analyze_paper, cross_examine_claim, synthesize_multiple_papers

    yield "event: status\ndata: " + json.dumps({"step": "analyzing"}) + "\n\n"
    await asyncio.sleep(0)

    # Build where-filter for Chroma if a source is selected
    where = {"source_name": source_filter} if source_filter else None

    try:
        if mode == "analyze":
            # Pull a broad set of chunks from the selected paper
            vs = get_vectorstore()
            raw = vs._collection.get(
                where=where,
                include=["documents", "metadatas"],
                limit=20,
            )
            chunks = [
                {"source": (m or {}).get("source_name", "paper"), "text": t, "metadata": m or {}}
                for t, m in zip(raw.get("documents", []), raw.get("metadatas", []))
            ]
            result = await analyze_paper(chunks)
            yield "event: muhaqqiq\ndata: " + json.dumps({"mode": "analyze", "data": result}) + "\n\n"

        elif mode == "cross_examine":
            # Retrieve relevant chunks for the claim
            scored = retrieve_with_threshold(
                question, candidate_k=12, final_k=8,
            )
            chunks = [
                {"source": doc.metadata.get("source_name", "paper"), "text": doc.page_content, "metadata": doc.metadata}
                for doc, _ in scored
                if not source_filter or doc.metadata.get("source_name") == source_filter
            ]
            result = await cross_examine_claim(question, chunks)
            yield "event: muhaqqiq\ndata: " + json.dumps({"mode": "cross_examine", "data": result}) + "\n\n"

        elif mode == "synthesize":
            # Group chunks per source and synthesize across all uploaded papers
            from app.rag.vectorstore import list_sources
            sources = list_sources()
            papers_data = []
            vs = get_vectorstore()
            for src in sources:
                raw = vs._collection.get(
                    where={"source_name": src["name"]},
                    include=["documents", "metadatas"],
                    limit=8,
                )
                papers_data.append({
                    "title": src["name"],
                    "chunks": [
                        {"text": t, "metadata": m or {}}
                        for t, m in zip(raw.get("documents", []), raw.get("metadatas", []))
                    ]
                })
            result = await synthesize_multiple_papers(papers_data)
            yield "event: muhaqqiq\ndata: " + json.dumps({"mode": "synthesize", "data": result}) + "\n\n"

        else:
            yield "event: muhaqqiq\ndata: " + json.dumps({"mode": mode, "data": {"error": f"Unknown mode: {mode}"}}) + "\n\n"

    except Exception as e:
        yield "event: muhaqqiq\ndata: " + json.dumps({"mode": mode, "data": {"error": str(e)}}) + "\n\n"

    yield "event: done\ndata: " + json.dumps({}) + "\n\n"



async def _stream_answer(question: str, history: list[dict]):
    """
    Legacy alias — kept so any external callers still work.
    Routes to Ustad by default.
    """
    async for chunk in _stream_ustad(question, history):
        yield chunk


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in req.history]
    agent = (req.agent or "ustad").lower()

    if agent == "muhaqqiq":
        gen = _stream_muhaqqiq(
            req.question,
            mode=req.muhaqqiq_mode or "analyze",
            source_filter=req.source_filter,
        )
    else:
        gen = _stream_ustad(req.question, history)

    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Upload notes
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=UploadResponse)
def upload_notes(files: List[UploadFile] = File(...)):
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
        raw = f.file.read()
        assert_file_size_ok(raw)

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


# ---------------------------------------------------------------------------
# Quiz (Imtehaan)
# ---------------------------------------------------------------------------
@router.post("/quiz/start")
async def quiz_start(req: QuizStartRequest):
    """
    Start a quiz session. Retrieves relevant study chunks for the topic
    and forwards them to Agent 4 (Imtehaan).
    """
    from app.rag.vectorstore import retrieve_with_threshold
    from app.agents.imtehaan import start_quiz
    from fastapi import HTTPException
    from app.core.logging import get_logger
    
    log = get_logger(__name__)
    
    log.info(f"Quiz start request: topic={req.topic}")
    
    # Check if we have any study notes
    if collection_count() == 0:
        log.warning("Quiz start failed: empty knowledge base")
        raise HTTPException(
            status_code=400,
            detail="Your knowledge base is empty! Please upload study notes (PDF, DOCX, TXT) first."
        )
    
    # Retrieve top 8 candidates for the topic, optionally scoped to one source
    log.info(f"Retrieving chunks for topic: {req.topic}, source_filter={req.source_filter}")

    if req.source_filter:
        # Pull directly from Chroma with a metadata filter, then rank by similarity
        from app.rag.vectorstore import get_vectorstore
        vs = get_vectorstore()
        raw = vs._collection.get(
            where={"source_name": req.source_filter},
            include=["documents", "metadatas"],
            limit=20,
        )
        chunks = [
            {"source": (m or {}).get("source_name", req.source_filter), "text": t}
            for t, m in zip(raw.get("documents", []), raw.get("metadatas", []))
        ][:8]
    else:
        scored_docs = retrieve_with_threshold(req.topic, candidate_k=15, final_k=8)
        log.info(f"Retrieved {len(scored_docs)} chunks")
        chunks = [
            {
                "source": doc.metadata.get("source_name", "notes"),
                "text": doc.page_content
            }
            for doc, _ in scored_docs
        ]
    
    log.info(f"Starting quiz with {len(chunks)} chunks")
    res = await start_quiz(req.topic, chunks)
    log.info(f"Quiz start result: {res}")
    if "error" in res:
        log.error(f"Quiz start error: {res['error']}")
        raise HTTPException(status_code=500, detail=res["error"])
        
    return res


@router.post("/quiz/answer")
async def quiz_answer(req: QuizAnswerRequest):
    """
    Evaluate a quiz answer using Agent 4 (Imtehaan).
    """
    from app.agents.imtehaan import evaluate_answer
    from fastapi import HTTPException
    
    res = await evaluate_answer(req.session_id, req.question_num, req.answer)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
        
    return res
