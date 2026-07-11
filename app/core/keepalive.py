"""
Keep-alive pinger for Render's free tier.

Render free web services sleep after ~15 minutes of inactivity. Pinging our
own /api/health endpoint every 10 minutes keeps the service warm.

NOTE: this only helps on Render (and similar). It does not work around the
ephemeral filesystem — see DEPLOYMENT.md for the persistent-disk option.

Only started if KEEP_ALIVE_ENABLED=true in the environment.
"""
from __future__ import annotations

import threading

import urllib.request

from app.core.logging import get_logger

log = get_logger(__name__)

_PING_INTERVAL = 600  # 10 minutes


def _loop(url: str) -> None:
    import time

    health_url = url.rstrip("/") + "/api/health"
    while True:
        try:
            with urllib.request.urlopen(health_url, timeout=20) as r:
                log.debug(f"keep-alive ping -> {r.status}")
        except Exception as e:  # noqa: BLE001
            log.debug(f"keep-alive ping failed: {e}")
        time.sleep(_PING_INTERVAL)


def start_keep_alive(base_url: str) -> None:
    t = threading.Thread(target=_loop, args=(base_url,), daemon=True, name="keep-alive")
    t.start()
    log.info(f"Keep-alive started -> {base_url}/api/health every {_PING_INTERVAL}s")
