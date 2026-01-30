"""Structured logging with JSON format and request ID tracking."""

import json
import logging
import sys
import os
from datetime import datetime, timezone

from google_mcp_core.utils.context import get_request_id


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self._format_time(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request_id if present
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)

    @staticmethod
    def _format_time(record: logging.LogRecord) -> str:
        """Format timestamp as ISO 8601 with Z suffix."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def setup_structured_logging(verbose: bool = False) -> None:
    """
    Configure structured logging globally.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
    """
    # Determine if JSON or text format
    use_json = os.getenv("GOOGLE_PERSONAL_MCP_JSON_LOGS", "").lower() in ("1", "true", "yes")

    if use_json:
        formatter = JSONFormatter()
    else:
        # Keep simple text format
        formatter = logging.Formatter("[%(levelname)s] %(message)s")

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Suppress noisy logs
    logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("google_auth_httplib2").setLevel(logging.WARNING)
