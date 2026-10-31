"""Structured JSON logging for request metadata."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

_LOG_FIELDS = ("request_id", "method", "path", "status_code", "duration_ms", "error_type")


class JsonFormatter(logging.Formatter):
    """Format log records as JSON without serializing arbitrary record fields."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize safe standard fields and explicitly allowed metadata."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _LOG_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), default=str)


logger = logging.getLogger("grievance")


def configure_logging(level: str) -> None:
    """Configure application/server logs as JSON and disable unsafe access logs."""
    for configured_logger in (logger, logging.getLogger("uvicorn.error")):
        configured_logger.setLevel(level)
        configured_logger.propagate = False
        if not configured_logger.handlers:
            configured_logger.addHandler(logging.StreamHandler())
        for handler in configured_logger.handlers:
            handler.setFormatter(JsonFormatter())
    logging.getLogger("uvicorn.access").disabled = True
