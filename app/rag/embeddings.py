from __future__ import annotations

import os
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_embeddings():
    provider = os.getenv("EMBEDDINGS_PROVIDER", settings.embeddings_provider).lower()

    if provider == "google":
        return _get_google_embeddings()
    return _get_local_embeddings()


def _get_google_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY", "")
    model = "models/embedding-001"
    log.info(f"Using Google embeddings: {model}")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=api_key,
    )
    dim = len(embeddings.embed_query("dimension probe"))
    log.info(f"Google embeddings ready (dim={dim})")
    return embeddings


def _get_local_embeddings():
    from langchain_community.embeddings import FastEmbedEmbeddings

    model_name = settings.embedding_model_name
    log.info(f"Loading embeddings model via FastEmbed: {model_name}")
    embeddings = FastEmbedEmbeddings(
        model_name=model_name,
        max_length=512,
        embed_kwargs={"normalize_embeddings": True},
    )
    dim = len(embeddings.embed_query("dimension probe"))
    log.info(f"Local embeddings model ready (dim={dim})")
    return embeddings
