"""
Unit tests for audit logging.
"""

import json
import time

import pytest

from slack_notifications.logging.audit import AuditLogger


class TestAuditLogger:
    """Tests for AuditLogger."""

    def test_audit_logger_creation(self, temp_audit_log):
        """Test creating audit logger."""
        logger = AuditLogger(log_file=temp_audit_log)

        assert logger.log_file == temp_audit_log
        assert logger.log_file.exists()

    def test_log_tool_call_success(self, temp_audit_log):
        """Test logging successful tool call."""
        logger = AuditLogger(log_file=temp_audit_log)

        logger.log_tool_call(
            tool_name="send_slack_message",
            parameters={"message": "test", "channel": "#test"},
            request_id="req-123",
            success=True,
            duration_ms=45.67,
        )

        # Read the log
        with open(temp_audit_log, "r") as f:
            entry = json.loads(f.readline())

        assert entry["tool_name"] == "send_slack_message"
        assert entry["request_id"] == "req-123"
        assert entry["success"] is True
        assert entry["duration_ms"] == 45.67
        assert entry["parameters"]["message"] == "test"

    def test_log_tool_call_failure(self, temp_audit_log):
        """Test logging failed tool call."""
        logger = AuditLogger(log_file=temp_audit_log)

        logger.log_tool_call(
            tool_name="send_slack_message",
            parameters={"message": "test"},
            request_id="req-456",
            success=False,
            error_message="Connection failed",
            duration_ms=12.34,
        )

        # Read the log
        with open(temp_audit_log, "r") as f:
            entry = json.loads(f.readline())

        assert entry["success"] is False
        assert entry["error_message"] == "Connection failed"

    def test_timer_functions(self, temp_audit_log):
        """Test audit logger timer functions."""
        logger = AuditLogger(log_file=temp_audit_log)

        start = logger.start_timer()
        time.sleep(0.01)  # Sleep 10ms
        duration = logger.stop_timer(start)

        assert duration >= 10  # At least 10ms
        assert duration < 100  # Less than 100ms

    def test_credential_masking_in_audit_log(self, temp_audit_log, monkeypatch):
        """Test credentials are masked in audit log."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        logger = AuditLogger(log_file=temp_audit_log)

        logger.log_tool_call(
            tool_name="configure_slack",
            parameters={"bot_token": "xoxb-123-456-secret"},
            request_id="req-789",
            success=True,
        )

        # Read the log
        with open(temp_audit_log, "r") as f:
            content = f.read()

        assert "xoxb-****-****" in content
        assert "secret" not in content
