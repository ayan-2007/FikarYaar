"""
Text splitter.

Uses token-based sizing (aligned with the embedding model's 256-token limit)
and structure-aware pre-splitting on section headings before recursive splits.
"""
from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.text_utils import clean_note_text, count_tokens, log_chunk_stats

log = get_logger(__name__)

# Structure-aware pre-split: numbered sections like "2. CLASSES" or "2.1 — ..."
_SECTION_SPLIT_RE = re.compile(
    r"(?=\n\d+\.\s+[A-Z][A-Z0-9\s/&-]{2,}|\n\d+\.\d+\s+[—–-]\s*)"
)


def _token_length(text: str) -> int:
    return count_tokens(text)


def get_splitter() -> RecursiveCharacterTextSplitter:
    """Return a token-aware recursive splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size_tokens,
        chunk_overlap=settings.chunk_overlap_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=_token_length,
        add_start_index=True,
    )


def _pre_split_by_sections(text: str) -> list[str]:
    """Split on major section headings when present."""
    parts = _SECTION_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def split_documents(documents: list[Document]) -> list[Document]:
    """Apply structure-aware + token-based splitting."""
    splitter = get_splitter()
    all_chunks: list[Document] = []

    for doc in documents:
        cleaned = clean_note_text(doc.page_content)
        if not cleaned:
            continue

        base_meta = dict(doc.metadata)
        sections = _pre_split_by_sections(cleaned)
        if len(sections) <= 1:
            sections = [cleaned]

        for section_text in sections:
            if _token_length(section_text) <= settings.chunk_size_tokens:
                chunk = Document(page_content=section_text, metadata=dict(base_meta))
                all_chunks.append(chunk)
                continue

            for chunk in splitter.split_documents(
                [Document(page_content=section_text, metadata=dict(base_meta))]
            ):
                all_chunks.append(chunk)

    # Stable chunk indices for debugging/citations
    per_source: dict[str, int] = {}
    for chunk in all_chunks:
        src = chunk.metadata.get("source_name", "note")
        idx = per_source.get(src, 0)
        chunk.metadata["chunk_index"] = idx
        per_source[src] = idx + 1

    log_chunk_stats(all_chunks, "split")
    return all_chunks
