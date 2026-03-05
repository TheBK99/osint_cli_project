"""Structured logging setup for investigation traceability."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging() -> None:
    """Configure structlog and standard logging for CLI usage."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def get_logger(name: str):
    """Return a configured structured logger instance."""
    return structlog.get_logger(name)
