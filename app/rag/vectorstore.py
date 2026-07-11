"""
Chroma vector store.

Chroma is an embedded (file-based) vector database — perfect for this project:
no separate server to run, persists to a folder, fast enough for thousands of
chunks.

This module is the single place that knows about Chroma. Everything else just
calls `get_vectorstore()` or `get_retriever()`.
"""
from __future__ import annotations

from typing import List, Optional

from langchain_chroma import Chroma

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings import get_embeddings

log = get_logger(__name__)

_vectorstore: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    """
    Return the singleton Chroma vectorstore, creating it if needed.

    Uses lazy loading so importing this module never starts Chroma or
    downloads the embeddings model — that only happens when first used.
    """
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    persist_dir = settings.chroma_path
    persist_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Opening Chroma at {persist_dir} (collection={settings.chroma_collection_name})")
    _vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )
    return _vectorstore


def reset_vectorstore() -> None:
    """Drop the cached instance (used by tests / after wiping the DB)."""
    global _vectorstore
    _vectorstore = None


def collection_count() -> int:
    """How many chunks are currently stored?"""
    try:
        return get_vectorstore()._collection.count()
    except Exception as e:  # noqa: BLE001
        log.warning(f"Could not read collection count: {e}")
        return 0


def get_retriever(k: Optional[int] = None):
    """
    Return a retriever that returns the top-k most similar note chunks for a
    query. Default k comes from settings.
    """
    return get_vectorstore().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k or settings.top_k},
    )


def similarity_search_with_scores(query: str, k: Optional[int] = None):
    """Return (Document, L2 distance) pairs. Lower distance = more similar."""
    return get_vectorstore().similarity_search_with_score(
        query, k=k or settings.retrieval_candidate_k
    )


def retrieve_with_threshold(
    query: str,
    candidate_k: Optional[int] = None,
    final_k: Optional[int] = None,
    max_distance: Optional[float] = None,
) -> list[tuple]:
    """
    Retrieve candidate chunks, filter by L2 distance threshold, return top-k.

    Chroma uses L2 distance on normalized embeddings (lower = better match).

    FALLBACK: if the threshold filters out every candidate, we fall back to
    returning the best `final_k` results regardless — the LLM grader downstream
    will discard truly irrelevant ones. This prevents the threshold from causing
    false "no notes found" responses when a question is slightly paraphrased.
    """
    candidate_k = candidate_k or settings.retrieval_candidate_k
    final_k = final_k or settings.top_k
    max_distance = max_distance if max_distance is not None else settings.retrieval_max_distance

    scored = similarity_search_with_scores(query, k=candidate_k)
    if not scored:
        return []

    filtered = [(doc, score) for doc, score in scored if score <= max_distance]

    if not filtered:
        # All candidates exceeded the threshold. Fall back to top-k by score so
        # the downstream LLM grader can make the final relevance decision.
        log.warning(
            f"All {len(scored)} candidates exceeded max_distance={max_distance:.3f}; "
            f"falling back to top-{final_k} by score (best={scored[0][1]:.4f})"
        )
        return scored[:final_k]

    return filtered[:final_k]


def delete_by_source(source_name: str) -> None:
    """
    Delete every chunk that came from a given file. Useful when a user wants to
    re-upload the same note (we remove the old version first).
    """
    vs = get_vectorstore()
    try:
        # Chroma filters on metadata
        ids = vs._collection.get(where={"source_name": source_name}).get("ids", [])
        if ids:
            vs._collection.delete(ids=ids)
            log.info(f"Deleted {len(ids)} chunk(s) for source '{source_name}'")
    except Exception as e:  # noqa: BLE001
        log.error(f"Failed to delete source '{source_name}': {e}")


def list_sources() -> List[dict]:
    """Return a summary of distinct source files present in the store."""
    try:
        all_meta = get_vectorstore()._collection.get(include=["metadatas"])
        seen = {}
        for m in all_meta.get("metadatas", []):
            if not m:
                continue
            name = m.get("source_name", "unknown")
            entry = seen.setdefault(name, {"name": name, "chunks": 0, "type": m.get("file_type", "?")})
            entry["chunks"] += 1
        return sorted(seen.values(), key=lambda x: x["name"].lower())
    except Exception as e:  # noqa: BLE001
        log.warning(f"Could not list sources: {e}")
        return []
