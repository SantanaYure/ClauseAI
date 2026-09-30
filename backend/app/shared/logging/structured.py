"""Small JSON logger setup for local development and future observability."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.shared.logging.context import get_log_context
from app.shared.logging.privacy import error_fields


class StructuredJsonFormatter(logging.Formatter):
    """Serialize log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **get_log_context(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            # Only type and frames: third-party messages may quote personal data.
            payload.update(error_fields(record.exc_info[1]))
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger once with the structured formatter."""

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger using the application logging configuration."""

    return logging.getLogger(name)
