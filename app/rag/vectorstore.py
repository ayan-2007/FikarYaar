"""
Vector store abstraction.

Supports two backends:
  - Chroma (local, file-based) — for Docker/Render/single-server deploys
  - Pinecone (cloud, managed) — for Vercel/serverless deploys

Switch via VECTOR_STORE env var or settings.vector_store.
"""
from __future__ import annotations

import os
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_vectorstore = None
_store_type: str | None = None


def _vs_type() -> str:
    return os.getenv("VECTOR_STORE", settings.vector_store).lower()


def get_vectorstore():
    global _vectorstore, _store_type
    vtype = _vs_type()
    if _vectorstore is not None and _store_type == vtype:
        return _vectorstore

    if vtype == "pinecone":
        _vectorstore = _init_pinecone()
    else:
        _vectorstore = _init_chroma()
    _store_type = vtype
    return _vectorstore


def reset_vectorstore() -> None:
    global _vectorstore, _store_type
    _vectorstore = None
    _store_type = None


# ── Chroma ──────────────────────────────────────────────────────────────────

def _init_chroma():
    from langchain_chroma import Chroma
    from app.rag.embeddings import get_embeddings

    persist_dir = settings.chroma_path
    persist_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Opening Chroma at {persist_dir} (collection={settings.chroma_collection_name})")
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def _chroma_count(vs) -> int:
    try:
        return vs._collection.count()
    except Exception:
        return 0


def _chroma_delete_source(vs, source_name: str) -> None:
    ids = vs._collection.get(where={"source_name": source_name}).get("ids", [])
    if ids:
        vs._collection.delete(ids=ids)


def _chroma_list_sources(vs) -> List[dict]:
    all_meta = vs._collection.get(include=["metadatas"])
    seen = {}
    for m in all_meta.get("metadatas", []):
        if not m:
            continue
        name = m.get("source_name", "unknown")
        entry = seen.setdefault(name, {"name": name, "chunks": 0, "type": m.get("file_type", "?")})
        entry["chunks"] += 1
    return sorted(seen.values(), key=lambda x: x["name"].lower())


# ── Pinecone ─────────────────────────────────────────────────────────────────

def _init_pinecone():
    from pinecone import Pinecone
    from langchain_pinecone import PineconeVectorStore
    from app.rag.embeddings import get_embeddings

    api_key = settings.pinecone_api_key or os.getenv("PINECONE_API_KEY", "")
    index_name = settings.pinecone_index_name or "fikaryaar"
    log.info(f"Connecting to Pinecone index: {index_name}")
    pc = Pinecone(api_key=api_key)
    return PineconeVectorStore(
        index=pc.Index(index_name),
        embedding=get_embeddings(),
        text_key="text",
    )


def _pinecone_count(vs) -> int:
    try:
        stats = vs._index.describe_index_stats()
        return stats.get("total_vector_count", 0)
    except Exception:
        return 0


def _pinecone_delete_source(vs, source_name: str) -> None:
    try:
        vs._index.delete(filter={"source_name": {"$eq": source_name}})
        log.info(f"Deleted vectors for source '{source_name}'")
    except Exception as e:
        log.error(f"Failed to delete source '{source_name}': {e}")


def _pinecone_list_sources(vs) -> List[dict]:
    try:
        stats = vs._index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        seen = {}
        for ns_name, ns_data in namespaces.items():
            if ns_name:
                seen[ns_name] = {"name": ns_name, "chunks": ns_data.get("vector_count", 0), "type": "?"}
        if not seen:
            seen["default"] = {
                "name": "default",
                "chunks": stats.get("total_vector_count", 0),
                "type": "?",
            }
        return sorted(seen.values(), key=lambda x: x["name"].lower())
    except Exception:
        return []


# ── Unified public API ──────────────────────────────────────────────────────

def collection_count() -> int:
    try:
        vs = get_vectorstore()
        if _vs_type() == "pinecone":
            return _pinecone_count(vs)
        return _chroma_count(vs)
    except Exception as e:
        log.warning(f"Could not read collection count: {e}")
        return 0


def get_retriever(k: Optional[int] = None):
    vs = get_vectorstore()
    return vs.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k or settings.top_k},
    )


def similarity_search_with_scores(query: str, k: Optional[int] = None):
    """
    Return (Document, score) pairs.
    Chroma: L2 distance (lower = better), Pinecone: cosine similarity (higher = better).
    """
    vs = get_vectorstore()
    return vs.similarity_search_with_score(query, k=k or settings.retrieval_candidate_k)


def retrieve_with_threshold(
    query: str,
    candidate_k: Optional[int] = None,
    final_k: Optional[int] = None,
    max_distance: Optional[float] = None,
) -> list[tuple]:
    candidate_k = candidate_k or settings.retrieval_candidate_k
    final_k = final_k or settings.top_k
    max_dist = max_distance if max_distance is not None else settings.retrieval_max_distance

    scored = similarity_search_with_scores(query, k=candidate_k)
    if not scored:
        return []

    if _vs_type() == "pinecone":
        # Pinecone: cosine similarity, higher = better. Keep all, let grader filter.
        return scored[:final_k]

    # Chroma: L2 distance, lower = better
    filtered = [(doc, score) for doc, score in scored if score <= max_dist]
    if not filtered:
        log.warning(
            f"All {len(scored)} candidates exceeded max_distance={max_dist:.3f}; "
            f"falling back to top-{final_k} by score (best={scored[0][1]:.4f})"
        )
        return scored[:final_k]
    return filtered[:final_k]


def delete_by_source(source_name: str) -> None:
    try:
        vs = get_vectorstore()
        if _vs_type() == "pinecone":
            _pinecone_delete_source(vs, source_name)
        else:
            _chroma_delete_source(vs, source_name)
    except Exception as e:
        log.error(f"Failed to delete source '{source_name}': {e}")


def list_sources() -> List[dict]:
    try:
        vs = get_vectorstore()
        if _vs_type() == "pinecone":
            return _pinecone_list_sources(vs)
        return _chroma_list_sources(vs)
    except Exception as e:
        log.warning(f"Could not list sources: {e}")
        return []
