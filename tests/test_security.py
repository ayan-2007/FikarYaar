"""Tests for security helpers (no LLM/vector DB needed)."""
from app.core.security import (
    is_allowed_filename,
    safe_filename,
)


def test_allowed_extensions():
    assert is_allowed_filename("notes.pdf")
    assert is_allowed_filename("lec.DOCX")
    assert is_allowed_filename("readme.md")
    assert is_allowed_filename("data.txt")
    assert not is_allowed_filename("malware.exe")
    assert not is_allowed_filename("script.py")
    assert not is_allowed_filename("archive.zip")


def test_safe_filename_strips_paths():
    # path traversal is removed
    safe = safe_filename("../../etc/passwd.pdf")
    assert ".." not in safe
    assert safe.endswith(".pdf")
    assert "/" not in safe and "\\" not in safe


def test_safe_filename_special_chars():
    safe = safe_filename("my weird! file?.docx")
    assert "?" not in safe
    assert "!" not in safe
    assert safe.endswith(".docx")
