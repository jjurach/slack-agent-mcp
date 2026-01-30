"""Audit logging for operations (security, compliance)."""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs operations for audit trail (security, compliance)."""

    def __init__(self, enabled: bool = True, log_path: Optional[str] = None):
        """
        Initialize audit logger.

        Args:
            enabled: Whether audit logging is enabled
            log_path: Path to audit log file, or None for default location
        """
        self.enabled = enabled
        self.log_path = log_path or self._get_default_log_path()

        if self.enabled:
            self._ensure_log_file_exists()

    def _get_default_log_path(self) -> str:
        """Get default audit log path: ~/.config/google-personal-mcp/audit.log"""
        base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(base_dir, "google-personal-mcp", "audit.log")

    def _ensure_log_file_exists(self) -> None:
        """Create audit log file and parent directory if needed."""
        try:
            Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.log_path).touch(exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create audit log: {e}")

    def log_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        profile: str = "default",
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        records_affected: int = 0,
    ) -> None:
        """
        Log a tool invocation to audit log (without credentials).

        Args:
            tool_name: Name of tool called
            parameters: Tool parameters (will be sanitized)
            profile: Authentication profile used
            request_id: Request ID for tracing
            success: Whether tool call succeeded
            error_message: Error message if failed
            records_affected: Number of records affected by operation
        """
        if not self.enabled:
            return

        # Sanitize parameters before logging
        safe_params = self._sanitize_parameters(parameters)

        entry = {
            "timestamp": self._format_timestamp(),
            "event_type": "tool_invocation",
            "tool_name": tool_name,
            "profile": profile,
            "request_id": request_id,
            "parameters": safe_params,
            "success": success,
            "error_message": error_message,
            "records_affected": records_affected,
        }

        self._write_entry(entry)

    def log_authentication(self, profile: str, success: bool, reason: Optional[str] = None) -> None:
        """
        Log authentication event.

        Args:
            profile: Profile being authenticated
            success: Whether authentication succeeded
            reason: Reason for authentication (new, refresh, expired scopes, etc.)
        """
        if not self.enabled:
            return

        entry = {
            "timestamp": self._format_timestamp(),
            "event_type": "authentication",
            "profile": profile,
            "success": success,
            "reason": reason,
        }

        self._write_entry(entry)

    def log_access_denied(
        self, profile: str, resource_type: str, resource_id: str, reason: str
    ) -> None:
        """
        Log access denied event.

        Args:
            profile: Profile that was denied
            resource_type: Type of resource (sheet, folder, etc.)
            resource_id: ID of resource (will be masked)
            reason: Reason for denial
        """
        if not self.enabled:
            return

        entry = {
            "timestamp": self._format_timestamp(),
            "event_type": "access_denied",
            "profile": profile,
            "resource_type": resource_type,
            "resource_id": "***ID_REDACTED***",
            "reason": reason,
        }

        self._write_entry(entry)

    @staticmethod
    def _sanitize_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove/mask sensitive parameters before logging.

        Args:
            params: Parameters to sanitize

        Returns:
            Sanitized parameters safe for logging
        """
        safe = {}
        sensitive_keys = {
            "content",
            "local_path",
            "access_token",
            "refresh_token",
            "credentials",
            "password",
            "secret",
        }

        for key, value in params.items():
            if key in sensitive_keys:
                # Log type and size but not content
                safe[key] = f"<{type(value).__name__}: {len(str(value))} chars>"
            else:
                # Safe to log
                safe[key] = value

        return safe

    @staticmethod
    def _format_timestamp() -> str:
        """Get current timestamp in ISO 8601 format with Z suffix."""
        dt = datetime.now(tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """
        Write entry to audit log (append-only, handles log rotation).

        Args:
            entry: Log entry to write
        """
        if not self.enabled:
            return

        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
