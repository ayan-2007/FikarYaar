"""
Security helpers for the upload endpoint.

Goals:
  * Only allow safe, study-related file types.
  * Enforce size + count limits.
  * Sanitise filenames so a malicious upload cannot escape data/uploads.
  * Reject disguised payloads (e.g. an .exe renamed to .pdf).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from app.core.config import settings

# Allow-list of extensions we actually parse. Everything else is rejected.
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".md": "text/markdown",
    ".txt": "text/plain",
}

# Small magic-byte sniffing for the most commonly abused types.
# (Extension-only checks are not enough — they can be spoofed.)
MAGIC_BYTES = {
    ".pdf": b"%PDF-",
    # DOCX and PPTX are both ZIP archives
    ".docx": b"PK\x03\x04",
    ".pptx": b"PK\x03\x04",
}


def is_allowed_filename(filename: str) -> bool:
    """True if the extension is on the allow-list."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def assert_upload_safe(files: list, content_lengths: list[int] | None = None) -> None:
    """
    Validate a batch of uploads. Raises HTTPException(400) on any violation.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    if len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum is {settings.max_upload_files}.",
        )

    total = 0
    for f in files:
        name = f.filename or ""
        if not is_allowed_filename(name):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed: {name}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
            )
        # FastAPI exposes the size on the UploadFile after we read it; we also
        # accept an explicit size list (read from the multipart header).
    if content_lengths:
        for size in content_lengths:
            total += size
        if total > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Total upload too large. Maximum is "
                f"{settings.max_upload_bytes // (1024 * 1024)} MB.",
            )


def assert_file_size_ok(file_bytes: bytes) -> None:
    """Check the actual byte length of a single uploaded file."""
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"{len(file_bytes) // (1024 * 1024)} MB file exceeds the "
            f"{settings.max_upload_bytes // (1024 * 1024)} MB limit.",
        )


def assert_magic_bytes(ext: str, head: bytes) -> None:
    """Reject files whose first bytes don't match their claimed type."""
    expected = MAGIC_BYTES.get(ext.lower())
    if expected and not head.startswith(expected):
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match its extension ({ext}). "
            "Upload rejected for safety.",
        )


def safe_filename(filename: str) -> str:
    """
    Return a filesystem-safe filename.

    - Takes only the basename (no path traversal like ../../etc/passwd).
    - Replaces anything that isn't [A-Za-z0-9._-] with '_'.
    - Prefixes with a timestamp to avoid collisions.
    """
    import re
    import time

    name = Path(filename).name  # strip any directory component
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.strip("._") or "note"
    ts = int(time.time() * 1000)
    # keep max length sane
    stem = Path(name).stem[:60]
    suffix = Path(name).suffix.lower()
    return f"{ts}_{stem}{suffix}"
