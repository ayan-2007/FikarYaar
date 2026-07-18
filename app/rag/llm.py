"""
LLM client: Dynamic switching between Gemini and Groq.

We expose helper models that dynamically check for GEMINI_API_KEY (or GOOGLE_API_KEY)
and fallback to GROQ_API_KEY if needed.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

# Try to import both SDKs safely
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


def _get_api_key(provider: str) -> str:
    """Helper to fetch API keys from settings or environment variables."""
    if provider == "gemini":
        return settings.gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    elif provider == "groq":
        return settings.groq_api_key or os.getenv("GROQ_API_KEY") or ""
    return ""


@lru_cache(maxsize=16)
def get_llm(temperature: float = 0.2, streaming: bool = False, max_tokens: int = 1024) -> Any:
    """
    The main answer-generating LLM.
    Returns ChatGoogleGenerativeAI with ChatGroq as a fallback if both keys are present.
    If one fails (e.g., rate limits), LangChain automatically rotates to the next available model.
    """
    gemini_key = _get_api_key("gemini")
    groq_key = _get_api_key("groq")

    models = []

    if HAS_GEMINI and gemini_key and gemini_key != "your_gemini_api_key_here":
        model_name = settings.gemini_model or "gemini-2.0-flash-lite"
        log.info(f"Adding Gemini Chat Model: {model_name} (temp={temperature}, streaming={streaming})")
        models.append(ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=gemini_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
            timeout=30,
            max_retries=1, # Reduce retries on the individual model so it falls back faster
            streaming=streaming,
        ))

    if HAS_GROQ and groq_key and groq_key != "your_groq_api_key_here":
        model_name = settings.groq_model or "llama-3.1-8b-instant"
        log.info(f"Adding Groq Chat Model: {model_name} (temp={temperature}, streaming={streaming})")
        models.append(ChatGroq(
            model=model_name,
            api_key=groq_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30,
            max_retries=1,
            streaming=streaming,
        ))

    if not models:
        raise ValueError(
            "Neither GEMINI_API_KEY nor GROQ_API_KEY is configured in your environment or .env file. "
            "Please provide at least one valid key to use Fikaryaar."
        )

    # If we have both, set the second as a fallback for the first!
    primary_model = models[0]
    if len(models) > 1:
        primary_model = primary_model.with_fallbacks(models[1:])
        log.info("API Fallback rotation enabled (will switch models if rate limited).")

    return primary_model


@lru_cache(maxsize=16)
def get_grader_llm() -> Any:
    """
    Small/fast model call used for intent classification and document relevance grading.
    Uses temperature=0.0 and low max_tokens for speed and consistency.
    """
    # Grader uses get_llm with temp=0.0 and low token cap
    return get_llm(temperature=0.0, max_tokens=16)


@lru_cache(maxsize=16)
def get_rewrite_llm() -> Any:
    """
    LLM used specifically for question rewriting.
    Uses temperature=0.0 and moderate max_tokens.
    """
    return get_llm(temperature=0.0, max_tokens=200)


@lru_cache(maxsize=16)
def get_quiz_llm() -> Any:
    """
    LLM used specifically for quiz question generation and assessment.
    Uses a higher temperature (0.7) for more creative and diverse questions.
    """
    return get_llm(temperature=0.7, max_tokens=3000)


def has_api_key() -> bool:
    """Returns True if any valid key is configured."""
    gemini_key = _get_api_key("gemini")
    groq_key = _get_api_key("groq")
    return bool(
        (gemini_key and gemini_key != "your_gemini_api_key_here") or
        (groq_key and groq_key != "your_groq_api_key_here")
    )
