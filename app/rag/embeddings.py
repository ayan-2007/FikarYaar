"""
Embeddings: a local sentence-transformers model.

This runs entirely on your machine (no API key, no cost). On first use it
downloads the model (~90 MB for all-MiniLM-L6-v2) and caches it; afterwards it
loads from cache in a couple of seconds.

We cache the model instance per-process so we don't reload it on every request.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_embeddings():
    """
    Build (once) and return the HuggingFace sentence-transformers embeddings.

    Wrapped in lru_cache so the model loads only once per process — reloading
    a 90 MB model on every request would be slow and waste memory.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = settings.embedding_model_name
    log.info(f"Loading embeddings model: {model_name} (first run downloads it)")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},  # CPU is fine and portable
        encode_kwargs={"normalize_embeddings": True},
    )
    dim = len(embeddings.embed_query("dimension probe"))
    log.info(f"Embeddings model ready (dim={dim}, normalized=True, metric=L2/cosine-equivalent)")
    return embeddings
