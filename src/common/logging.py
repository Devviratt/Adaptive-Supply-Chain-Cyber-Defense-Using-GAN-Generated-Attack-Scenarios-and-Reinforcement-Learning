"""
ASCCD Structured Logging.

Provides consistent structured logging across the application using structlog.
Supports JSON output for production and console output for development.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from src.common.config import get_settings


def setup_logging(log_level: str | None = None, log_format: str | None = None) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Override format ('json' or 'console').
    """
    settings = get_settings()
    level = getattr(logging, (log_level or settings.log_level).upper(), logging.INFO)
    fmt = log_format or settings.log_format

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Shared processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if fmt == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Apply formatter to root handler
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        Configured structlog BoundLogger.
    """
    return structlog.get_logger(name)
