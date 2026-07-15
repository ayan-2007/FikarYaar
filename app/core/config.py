"""
Application configuration.

All settings are read from environment variables (or a local `.env` file).
Using pydantic-settings gives us:
  * type validation,
  * a single source of truth (`settings`),
  * safe defaults,
  * and `.env` loading for free.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = the folder that contains this app/ package (two levels up).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Strongly-typed app configuration loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- LLM (Groq, free tier) ----
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # ---- LLM (Gemini, free tier) ----
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # ---- Embeddings (local sentence-transformers, free) ----
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ---- Vector store (Chroma, file-based) ----
    chroma_persist_dir: str = "data/chroma_db"
    chroma_collection_name: str = "study_notes"

    # ---- Knowledge sources ----
    notes_dir: str = "pdf"
    upload_dir: str = "data/uploads"

    # ---- Retrieval tuning ----
    top_k: int = 7
    retrieval_candidate_k: int = 25
    # Chroma L2 distance on normalized embeddings. Lower = more similar.
    # Tested values: strong match ~0.6-0.9, moderate match ~1.0-1.4,
    # off-topic (France capital) ~1.6+. Threshold of 1.5 captures relevant
    # notes while the downstream LLM grader filters any remaining noise.
    retrieval_max_distance: float = 1.5
    chunk_size_tokens: int = 220
    chunk_overlap_tokens: int = 30
    chunk_min_chars: int = 80
    chunk_min_tokens: int = 25
    log_prompts: bool = True

    # ---- Server ----
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # ---- Upload security ----
    max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB
    max_upload_files: int = 10

    # ---- Keep-alive (Render free-tier anti-sleep) ----
    keep_alive_enabled: bool = False
    keep_alive_url: str = ""

    # ---- Runtime flags (derived, not from env) ----
    is_cloud: bool = False

    # ------------------------------------------------------------------
    # Validators / helpers that resolve relative paths against PROJECT_ROOT
    # ------------------------------------------------------------------
    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        # Allow either a JSON list or a comma-separated string in .env
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json

                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def resolve(self, relative: str) -> Path:
        """Resolve a project-relative path to an absolute Path."""
        p = Path(relative)
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    @property
    def chroma_path(self) -> Path:
        return self.resolve(self.chroma_persist_dir)

    @property
    def notes_path(self) -> Path:
        return self.resolve(self.notes_dir)

    @property
    def uploads_path(self) -> Path:
        return self.resolve(self.upload_dir)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton (constructed once per process)."""
    s = Settings()

    # Detect common free-tier cloud providers so we can adapt behavior.
    import os

    s.is_cloud = any(
        os.getenv(var)
        for var in ("RENDER", "RENDER_EXTERNAL_URL", "DYNO", "RAILWAY_PROJECT_ID")
    )
    return s


# Single importable instance used everywhere in the app.
settings = get_settings()
