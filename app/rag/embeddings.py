from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_embeddings():
    from langchain_community.embeddings import FastEmbedEmbeddings

    model_name = settings.embedding_model_name
    log.info(f"Loading embeddings model via FastEmbed: {model_name}")
    embeddings = FastEmbedEmbeddings(
        model_name=model_name,
        max_length=512,
        embed_kwargs={"normalize_embeddings": True},
    )
    dim = len(embeddings.embed_query("dimension probe"))
    log.info(f"Embeddings model ready (dim={dim})")
    return embeddings
