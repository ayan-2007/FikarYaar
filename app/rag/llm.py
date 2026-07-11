"""
LLM client: Groq via langchain-groq.

We expose three helper models:
  * get_llm()         -> the main chat model used for final answers
  * get_grader_llm()  -> a small/cheap call used for intent + relevance grading
  * get_rewrite_llm() -> a mid-sized call used for question rewriting (needs
                         enough tokens for a full sentence, not just a word)
"""
from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


@lru_cache
def get_llm() -> ChatGroq:
    """The main answer-generating LLM."""
    log.info(f"Initializing Groq chat model: {settings.groq_model}")
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.2,        # low temperature = more faithful to the notes
        max_tokens=1024,
        timeout=30,
        max_retries=2,
    )


@lru_cache
def get_grader_llm() -> ChatGroq:
    """
    Small/fast model for the guardrail checks (intent + doc relevance).
    Lower max tokens because we only expect ONE word back.
    """
    return ChatGroq(
        model=settings.groq_model,  # same model; graders just use few tokens
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=5,
        timeout=20,
        max_retries=2,
    )


@lru_cache
def get_rewrite_llm() -> ChatGroq:
    """
    LLM used specifically for question rewriting.

    Unlike the grader (max_tokens=5), rewrites need enough tokens to produce a
    full self-contained question sentence (up to ~200 tokens). Using the grader
    here was the primary cause of truncated/broken rewritten questions.
    """
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=200,
        timeout=20,
        max_retries=2,
    )


def has_api_key() -> bool:
    return bool(settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here")
