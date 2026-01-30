"""
Audit logging for MCP tool calls.

Tracks all MCP tool invocations with parameters, results, and timing
for debugging and compliance purposes.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.sanitizer import sanitize_dict, should_sanitize


class AuditLogger:
    """
    Audit logger for MCP tool calls.

    Writes structured audit logs to a file tracking all tool invocations,
    parameters, success/failure status, and timing information.
    """

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file. If None, uses default location.
        """
        if log_file is None:
            # Default location: ~/.config/slack-agent/audit.log
            config_dir = Path.home() / ".config" / "slack-agent"
            config_dir.mkdir(parents=True, exist_ok=True)
            log_file = config_dir / "audit.log"

        self.log_file = log_file
        self.logger = logging.getLogger("slack_notifications.audit")

        # Configure file handler for audit log
        self._configure_handler()

    def _configure_handler(self) -> None:
        """Configure file handler for audit logging."""
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter("%(message)s"))  # JSON only
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger

    def log_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        request_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """
        Log a tool call to the audit log.

        Args:
            tool_name: Name of the MCP tool
            parameters: Tool parameters (will be sanitized)
            request_id: Unique request ID
            success: Whether the tool call succeeded
            error_message: Error message if failed
            duration_ms: Execution duration in milliseconds
        """
        # Sanitize parameters
        safe_params = sanitize_dict(parameters) if should_sanitize() else parameters

        # Build audit entry
        entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "tool_name": tool_name,
            "parameters": safe_params,
            "success": success,
        }

        if error_message:
            entry["error_message"] = error_message

        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)

        # Write to audit log
        self.logger.info(json.dumps(entry))

    def start_timer(self) -> float:
        """
        Start a timer for measuring tool call duration.

        Returns:
            Start time in seconds (use with stop_timer)
        """
        return time.time()

    def stop_timer(self, start_time: float) -> float:
        """
        Stop a timer and calculate duration.

        Args:
            start_time: Start time from start_timer()

        Returns:
            Duration in milliseconds
        """
        return (time.time() - start_time) * 1000


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """
    Get the global audit logger instance.

    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
