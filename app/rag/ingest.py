"""
Ingestion pipeline: documents -> chunks -> embeddings -> Chroma.

This is the "write" side of RAG. The "read" side is the retriever/graph in
`app.rag.graph`.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.loader import load_directory, load_single_file
from app.rag.splitter import split_documents
from app.rag.text_utils import filter_quality_chunks, log_chunk_stats, sanitize_metadata
from app.rag.vectorstore import delete_by_source, get_vectorstore, reset_vectorstore

log = get_logger(__name__)


def ingest_documents(documents: List[Document], source_name: str | None = None) -> int:
    """
    Split + filter + embed + store a list of Documents.

    Args:
        documents: pre-loaded LangChain Documents.
        source_name: if given, any existing chunks for this source are removed
                     first (so re-uploading a note replaces it cleanly).

    Returns:
        The number of chunks actually added.
    """
    if not documents:
        log.warning("ingest_documents called with no documents")
        return 0

    if source_name:
        delete_by_source(source_name)

    chunks = split_documents(documents)
    chunks, stats = filter_quality_chunks(chunks)
    log.info(
        f"[ingest] quality filter: input={stats['input']} kept={stats['kept']} "
        f"(empty={stats['empty']} short={stats['too_short']} toc={stats['toc']} "
        f"dup={stats['duplicate']})"
    )
    if not chunks:
        log.warning("No quality chunks after filtering — skipping")
        return 0

    for chunk in chunks:
        chunk.metadata = sanitize_metadata(chunk.metadata)

    log_chunk_stats(chunks, "ingest-final")

    base = source_name or documents[0].metadata.get("source_name", "note")
    ids = [f"{base}_{chunk.metadata.get('chunk_index', i)}" for i, chunk in enumerate(chunks)]

    vs = get_vectorstore()
    vs.add_documents(documents=chunks, ids=ids)
    log.info(f"Ingested {len(chunks)} chunk(s) from '{base}'")
    return len(chunks)


def ingest_file(path: Path) -> int:
    """Load a single file from disk and ingest it. Returns chunk count."""
    path = Path(path)
    docs = load_single_file(path)
    return ingest_documents(docs, source_name=path.name)


def ingest_files(paths: List[Path]) -> int:
    """Ingest many files; returns total chunks added."""
    total = 0
    for p in paths:
        try:
            total += ingest_file(Path(p))
        except Exception as e:  # noqa: BLE001
            log.error(f"Skipping {p}: {e}")
    return total


def wipe_vectorstore() -> None:
    """Delete the on-disk Chroma index and reset the in-process singleton."""
    shutil.rmtree(settings.chroma_path, ignore_errors=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    reset_vectorstore()
    log.info("Vector store wiped")


def ingest_all_sources() -> dict:
    """
    Full rebuild: wipe index, ingest bundled pdf/ notes and data/uploads/.

    Returns summary stats for evaluation scripts.
    """
    import hashlib

    wipe_vectorstore()

    total_chunks = 0
    files_processed = 0
    sources: list[str] = []
    seen_hashes: set[str] = set()

    def _file_hash(path: Path) -> str:
        h = hashlib.md5()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()

    def _ingest_path(path: Path, display_name: str) -> None:
        nonlocal total_chunks, files_processed
        digest = _file_hash(path)
        if digest in seen_hashes:
            log.info(f"Skipping duplicate file (same content): {display_name}")
            return
        seen_hashes.add(digest)

        docs = load_single_file(path)
        for d in docs:
            d.metadata["source_name"] = display_name
        added = ingest_documents(docs, source_name=display_name)
        total_chunks += added
        files_processed += 1
        sources.append(display_name)

    # Bundled notes
    if settings.notes_path.exists():
        for path in sorted(settings.notes_path.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {
                ".pdf", ".docx", ".md", ".txt", ".markdown", ".pptx"
            }:
                continue
            if path.name.upper() == "README.MD":
                continue
            try:
                _ingest_path(path, path.name)
            except Exception as e:  # noqa: BLE001
                log.error(f"Failed to ingest {path.name}: {e}")

    # User uploads (skip .gitkeep)
    upload_dir = settings.uploads_path
    if upload_dir.exists():
        for path in sorted(upload_dir.iterdir()):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in {".pdf", ".docx", ".md", ".txt", ".markdown", ".pptx"}:
                continue
            display = path.name
            if "_" in display and display.split("_", 1)[0].isdigit():
                display = display.split("_", 1)[1]
            try:
                _ingest_path(path, display)
            except Exception as e:  # noqa: BLE001
                log.error(f"Failed to ingest upload {path.name}: {e}")

    return {
        "files_processed": files_processed,
        "chunks_added": total_chunks,
        "sources": sorted(set(sources)),
    }


def ingest_notes_directory() -> int:
    """Ingest every supported file from the default notes/ directory."""
    notes = load_directory(settings.notes_path)
    if not notes:
        log.warning("No notes found in notes directory — nothing to ingest")
        return 0
    return ingest_documents(notes)
