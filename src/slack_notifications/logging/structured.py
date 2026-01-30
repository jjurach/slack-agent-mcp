"""
Structured logging configuration.

Provides logging setup with support for both text and JSON output formats.
"""

import json
import logging
import os
import sys
from typing import Optional


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses SLACK_AGENT_VERBOSE environment variable
    """
    if level is None:
        # Check for verbose mode
        if os.getenv("SLACK_AGENT_VERBOSE", "0") == "1":
            level = "DEBUG"
        else:
            level = "INFO"

    # Convert to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    if os.getenv("SLACK_AGENT_JSON_LOGS", "0") == "1":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON.

    Useful for log aggregation systems like ELK, Splunk, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log entry
        """
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "message", "pathname", "process", "processName", "relativeCreated",
                          "thread", "threadName", "exc_info", "exc_text", "stack_info"):
                log_data[key] = value

        return json.dumps(log_data)
