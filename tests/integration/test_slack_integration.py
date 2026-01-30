"""
Integration tests for Slack API.

These tests require real Slack credentials and will be skipped
if SLACK_BOT_TOKEN is not set.
"""

import os

import pytest
from slack_sdk.errors import SlackApiError

from slack_notifications.config import SlackConfig
from slack_notifications.notifier import SlackNotifier


pytestmark = pytest.mark.integration


@pytest.fixture
def skip_if_no_token():
    """Skip integration tests if Slack token not available."""
    if not os.getenv("SLACK_BOT_TOKEN"):
        pytest.skip("SLACK_BOT_TOKEN not set, skipping integration tests")


@pytest.fixture
def integration_config(skip_if_no_token):
    """Get configuration for integration tests."""
    return SlackConfig.from_env()


class TestSlackIntegration:
    """Integration tests with real Slack API."""

    def test_authentication(self, integration_config):
        """Test authentication with Slack API."""
        from slack_sdk import WebClient

        client = WebClient(token=integration_config.bot_token)
        response = client.auth_test()

        assert response["ok"] is True
        assert "user" in response
        assert "team" in response

    def test_send_message(self, integration_config):
        """Test sending a message to Slack."""
        notifier = SlackNotifier(config=integration_config)

        response = notifier.notify(
            message="Test message from integration test",
            level="info"
        )

        assert response.get("ok") is True
        assert "ts" in response

    def test_invalid_channel(self, integration_config):
        """Test error handling with invalid channel."""
        notifier = SlackNotifier(config=integration_config)

        with pytest.raises(Exception):
            notifier.notify(
                message="Test",
                channel="#nonexistent-channel-12345",
                level="info"
            )

    def test_list_channels(self, integration_config):
        """Test listing Slack channels."""
        from slack_sdk import WebClient

        client = WebClient(token=integration_config.bot_token)
        response = client.conversations_list(limit=10)

        assert response["ok"] is True
        assert "channels" in response
        assert len(response["channels"]) > 0
