from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.logging import get_logger

log = get_logger(__name__)

COUNTER_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "offtopic_count.json"
MAX_OFFTOPIC = 5


def _load() -> int:
    try:
        if COUNTER_FILE.exists():
            data = json.loads(COUNTER_FILE.read_text())
            return data.get("count", 0)
    except Exception as e:
        log.warning(f"Could not load counter: {e}")
    return 0


def _save(count: int) -> None:
    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        COUNTER_FILE.write_text(json.dumps({"count": count}))
    except Exception as e:
        log.warning(f"Could not save counter: {e}")


def remaining() -> int:
    return max(0, MAX_OFFTOPIC - _load())


def increment() -> int:
    count = _load() + 1
    _save(count)
    return count


def limit_reached() -> bool:
    return _load() >= MAX_OFFTOPIC
