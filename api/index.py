"""
Vercel serverless entry point.

On Vercel, each HTTP request spins up a fresh Python process. This module
imports the FastAPI app and wraps it with a Vercel-compatible handler.

The Vercel Python Runtime wraps ASGI apps via the `app` module-level variable.
"""
import os

os.environ.setdefault("VERCEL", "1")

from app.main import app  # noqa: E402
