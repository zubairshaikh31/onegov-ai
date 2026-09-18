"""
Structured logging configuration.
Uses loguru with JSON output in production, human-readable in development.
"""

import json
import logging
import sys
from typing import Any

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Intercepts standard library log records and routes them through loguru.
    This ensures that third-party libraries (SQLAlchemy, uvicorn, etc.)
    also use our structured logging format.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore[assignment]

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _json_formatter(record: dict[str, Any]) -> str:
    """Format log record as a JSON line for production ingestion."""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    if record["exception"]:
        exc = record["exception"]
        log_entry["exception"] = f"{exc.type.__name__}: {exc.value}" if hasattr(exc, "type") else str(exc)
    if record["extra"]:
        log_entry["extra"] = {k: str(v) for k, v in record["extra"].items()}
    raw_json = json.dumps(log_entry, default=str)
    return raw_json.replace("{", "{{").replace("}", "}}") + "\n"


def setup_logging() -> None:
    """
    Configure loguru and intercept stdlib loggers.
    Call this once at application startup in main.py.
    """
    # Remove default loguru sink
    logger.remove()

    if settings.LOG_FORMAT == "json":
        logger.add(sys.stdout, format=_json_formatter, level=settings.LOG_LEVEL)
    else:
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
                "<level>{message}</level>"
            ),
            level=settings.LOG_LEVEL,
            colorize=True,
        )

    # Intercept stdlib loggers
    intercept_handler = InterceptHandler()
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "sqlalchemy"]:
        log = logging.getLogger(name)
        log.handlers = [intercept_handler]
        log.propagate = False

    logging.basicConfig(handlers=[intercept_handler], level=0)
