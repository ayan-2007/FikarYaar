"""
Centralised logging built on loguru.

Why loguru instead of stdlib logging?
  * One line to configure, no boilerplate.
  * Beautiful coloured output in dev, JSON-ish in prod.
  * Rotation/retention built-in.

Every module does:  `from app.core.logging import get_logger; log = get_logger(__name__)`
"""
import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings

_CONFIGURED = False


def configure_logging() -> None:
    """Set up loguru sinks. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir = settings.resolve("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # clear default handler

    # Console: human-friendly, coloured. Less verbose in cloud.
    level = "INFO"
    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        ),
        backtrace=False,
        diagnose=False,  # never leak local variable values in prod
    )

    # File: rotating, kept for 7 days.
    logger.add(
        Path(log_dir) / "app.log",
        level="DEBUG",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,  # thread-safe, non-blocking
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    _CONFIGURED = True


def get_logger(name: str):
    """Return a logger bound to the given module name."""
    if not _CONFIGURED:
        configure_logging()
    return logger.bind(name=name)
