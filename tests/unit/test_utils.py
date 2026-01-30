"""
Unit tests for utility modules.
"""

import os

import pytest

from slack_notifications.utils import (
    clear_request_id,
    get_request_id,
    mask_credentials,
    set_request_id,
    should_sanitize,
)
from slack_notifications.utils.sanitizer import sanitize_dict


class TestRequestContext:
    """Tests for request ID context management."""

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        request_id = set_request_id()

        assert request_id is not None
        assert len(request_id) == 36  # UUID4 format
        assert get_request_id() == request_id

    def test_clear_request_id(self):
        """Test clearing request ID."""
        set_request_id()
        assert get_request_id() is not None

        clear_request_id()
        assert get_request_id() is None

    def test_unique_request_ids(self):
        """Test that each set_request_id() generates unique IDs."""
        id1 = set_request_id()
        clear_request_id()
        id2 = set_request_id()

        assert id1 != id2


class TestSanitizer:
    """Tests for credential sanitization."""

    def test_should_sanitize_default(self, monkeypatch):
        """Test sanitization is enabled by default."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)
        assert should_sanitize() is True

    def test_should_sanitize_debug_mode(self, monkeypatch):
        """Test sanitization is disabled in debug mode."""
        monkeypatch.setenv("SLACK_AGENT_DEBUG", "1")
        assert should_sanitize() is False

    def test_mask_bot_token(self, monkeypatch):
        """Test masking Slack bot tokens."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        text = "Token: xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx"
        masked = mask_credentials(text)

        assert "xoxb-****-****" in masked
        assert "abcdefghijklmnopqrstuvwx" not in masked

    def test_mask_user_token(self, monkeypatch):
        """Test masking Slack user tokens."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        text = "Token: xoxp-1234567890-1234567890-1234567890-abcdefghijklmnopqrstuvwx"
        masked = mask_credentials(text)

        assert "xoxp-****-****-****" in masked
        assert "abcdefghijklmnopqrstuvwx" not in masked

    def test_mask_webhook_url(self, monkeypatch):
        """Test masking Slack webhook URLs."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        text = "Webhook: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
        masked = mask_credentials(text)

        assert "https://hooks.slack.com/services/****" in masked
        assert "T00000000" not in masked

    def test_no_masking_in_debug_mode(self, monkeypatch):
        """Test credentials are not masked in debug mode."""
        monkeypatch.setenv("SLACK_AGENT_DEBUG", "1")

        text = "Token: xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx"
        masked = mask_credentials(text)

        assert masked == text

    def test_sanitize_dict(self, monkeypatch):
        """Test sanitizing dictionaries."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        data = {
            "token": "xoxb-1234567890-1234567890-abcdefghijklmnopqrstuvwx",
            "channel": "#general",
            "nested": {
                "webhook": "https://hooks.slack.com/services/T00/B00/XXX",
            },
            "list": ["xoxp-111-222-333-abc", "normal text"],
        }

        sanitized = sanitize_dict(data)

        assert "xoxb-****-****" in sanitized["token"]
        assert sanitized["channel"] == "#general"
        assert "https://hooks.slack.com/services/****" in sanitized["nested"]["webhook"]
        assert "xoxp-****-****-****" in sanitized["list"][0]
        assert sanitized["list"][1] == "normal text"

    def test_sanitize_preserves_non_credentials(self, monkeypatch):
        """Test sanitization doesn't affect non-credential text."""
        monkeypatch.delenv("SLACK_AGENT_DEBUG", raising=False)

        text = "This is a normal message with no credentials"
        masked = mask_credentials(text)

        assert masked == text
