"""
Text utilities for the ingestion and retrieval pipeline.

- clean_note_text: strip PDF/OCR noise before chunking
- token counting aligned with the embedding model's tokenizer
- chunk deduplication and quality filters
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import Iterable

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

# PDF bullet artifacts, e.g. (cid:127)
_CID_RE = re.compile(r"\(cid:\d+\)")
# Repeated page headers like "C++ MASTERY NOTES Page 12"
_PAGE_HEADER_RE = re.compile(
    r"^[^\n]{0,80}\bPage\s+\d+\s*\n?",
    re.IGNORECASE | re.MULTILINE,
)
# Table-of-contents style lines (mostly headings + bullets, little prose)
_TOC_LINE_RE = re.compile(r"^\s*(\d+\.)+\d*\s+[\w\s\-–—/]+$|^\s*\(cid:\d+\)\s*\d", re.MULTILINE)
# Section heading detector for structure-aware pre-splitting
_SECTION_HEADING_RE = re.compile(
    r"(?m)^(?:\d+\.\s+[A-Z][A-Z0-9\s/&-]{2,}|\d+\.\d+\s+[—–-]?\s*.+)$"
)


def clean_note_text(text: str) -> str:
    """Normalize study-note text before chunking/embedding."""
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = _CID_RE.sub("• ", text)
    text = text.replace("\ufffd", " ")
    text = _PAGE_HEADER_RE.sub("", text)
    # Collapse whitespace but keep paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_section_heading(text: str) -> str | None:
    """Return the first section-style heading in a chunk, if any."""
    for line in text.splitlines():
        line = line.strip()
        if _SECTION_HEADING_RE.match(line):
            return line[:120]
    return None


def is_likely_toc_chunk(text: str) -> bool:
    """
    Heuristic: table-of-contents chunks are mostly short lines / bullets and
    hurt retrieval precision for factual questions.
    """
    stripped = text.strip()
    if not stripped:
        return True
    upper = stripped.upper()
    if "TABLE OF CONTENTS" in upper and len(stripped) < 1500:
        return True

    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if len(lines) < 3:
        return False

    toc_like = sum(1 for ln in lines if _TOC_LINE_RE.match(ln) or ln.startswith("•"))
    return toc_like / len(lines) > 0.6 and len(stripped) < 1200


@lru_cache
def _get_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(settings.embedding_model_name)


def count_tokens(text: str) -> int:
    """Token count using the same tokenizer family as the embedding model."""
    if not text:
        return 0
    return len(_get_tokenizer().encode(text, add_special_tokens=False))


def content_fingerprint(text: str) -> str:
    """Stable hash for near-duplicate detection within a source."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def filter_quality_chunks(chunks: list[Document]) -> tuple[list[Document], dict]:
    """
    Drop empty, TOC-only, too-short, and duplicate chunks.

    Returns (kept_chunks, stats_dict).
    """
    stats = {
        "input": len(chunks),
        "empty": 0,
        "too_short": 0,
        "toc": 0,
        "duplicate": 0,
        "kept": 0,
    }
    if not chunks:
        return [], stats

    kept: list[Document] = []
    seen_hashes: set[str] = set()

    min_chars = settings.chunk_min_chars
    min_tokens = settings.chunk_min_tokens

    for chunk in chunks:
        text = clean_note_text(chunk.page_content)
        if not text:
            stats["empty"] += 1
            continue
        if len(text) < min_chars or count_tokens(text) < min_tokens:
            stats["too_short"] += 1
            continue
        if is_likely_toc_chunk(text):
            stats["toc"] += 1
            continue

        fp = content_fingerprint(text)
        if fp in seen_hashes:
            stats["duplicate"] += 1
            continue
        seen_hashes.add(fp)

        chunk.page_content = text
        heading = extract_section_heading(text)
        if heading:
            chunk.metadata["section"] = heading
        kept.append(chunk)

    stats["kept"] = len(kept)
    return kept, stats


def sanitize_metadata(metadata: dict) -> dict:
    """Keep only fields useful for retrieval debugging and UI citations."""
    allowed = {
        "source",
        "source_name",
        "file_type",
        "page",
        "slide",
        "section",
        "chunk_index",
        "start_index",
    }
    return {k: v for k, v in metadata.items() if k in allowed and v is not None}


def log_chunk_stats(chunks: Iterable[Document], label: str) -> None:
    """Log chunk length distribution for pipeline debugging."""
    chunks = list(chunks)
    if not chunks:
        log.info(f"[{label}] 0 chunks")
        return

    char_lens = [len(c.page_content) for c in chunks]
    token_lens = [count_tokens(c.page_content) for c in chunks]
    log.info(
        f"[{label}] {len(chunks)} chunks | "
        f"chars min/avg/max={min(char_lens)}/{sum(char_lens)//len(char_lens)}/{max(char_lens)} | "
        f"tokens min/avg/max={min(token_lens)}/{sum(token_lens)//len(token_lens)}/{max(token_lens)}"
    )
