"""
Structured debug logging for the RAG pipeline.

Every stage logs intermediate artifacts so retrieval/generation failures can be
traced upstream instead of guessed at.
"""
from __future__ import annotations

from typing import Iterable

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


def log_retrieval_results(question: str, scored_docs: list[tuple[Document, float]]) -> None:
    """Log top-k retrieved chunks with L2 distance scores (lower = better)."""
    log.info(f"[retrieve] question={question[:120]!r} candidates={len(scored_docs)}")
    for i, (doc, score) in enumerate(scored_docs, 1):
        src = doc.metadata.get("source_name", "?")
        section = doc.metadata.get("section", "")
        page = doc.metadata.get("page", "?")
        preview = doc.page_content[:160].replace("\n", " ")
        log.info(
            f"[retrieve] #{i} score={score:.4f} src={src} page={page} "
            f"section={section!r} | {preview}..."
        )


def log_graded_chunks(question: str, kept: list[Document], dropped: int) -> None:
    log.info(f"[grade] question={question[:120]!r} kept={len(kept)} dropped={dropped}")
    for i, doc in enumerate(kept, 1):
        src = doc.metadata.get("source_name", "?")
        section = doc.metadata.get("section", "")
        preview = doc.page_content[:120].replace("\n", " ")
        log.info(f"[grade] kept #{i} src={src} section={section!r} | {preview}...")


def log_final_prompt(system_text: str, human_text: str) -> None:
    if not settings.log_prompts:
        return
    log.debug(f"[prompt] SYSTEM ({len(system_text)} chars):\n{system_text[:4000]}")
    log.debug(f"[prompt] HUMAN ({len(human_text)} chars):\n{human_text[:2000]}")
