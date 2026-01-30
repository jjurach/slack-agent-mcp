"""
Shared pytest fixtures for testing slack-notifications.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from slack_notifications.config import ProfileConfig, SlackConfig


@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient with predefined responses."""
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {
        "ok": True,
        "ts": "1234567890.123456",
        "channel": "C1234567890",
    }
    mock_client.auth_test.return_value = {
        "ok": True,
        "user": "test-bot",
        "team": "Test Team",
        "user_id": "U1234567890",
    }
    mock_client.conversations_list.return_value = {
        "ok": True,
        "channels": [
            {"id": "C1111", "name": "general", "is_member": True, "is_private": False},
            {"id": "C2222", "name": "random", "is_member": False, "is_private": False},
        ]
    }
    return mock_client


@pytest.fixture
def mock_config():
    """Mock SlackConfig for testing."""
    return SlackConfig(
        bot_token="xoxb-test-token-1234567890",
        default_channel="#test",
        timeout=30,
        max_retries=3,
    )


@pytest.fixture
def mock_profile_config():
    """Mock ProfileConfig for testing."""
    return ProfileConfig(
        bot_token_env="SLACK_TEST_TOKEN",
        default_channel="#test",
        timeout=30,
        max_retries=3,
    )


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".config" / "slack-agent"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token-1234567890")
    monkeypatch.setenv("SLACK_DEFAULT_CHANNEL", "#test")
    monkeypatch.setenv("SLACK_TIMEOUT", "30")
    monkeypatch.setenv("SLACK_MAX_RETRIES", "3")


@pytest.fixture(autouse=True)
def cleanup_request_id():
    """Clean up request ID context after each test."""
    from slack_notifications.utils import clear_request_id
    yield
    clear_request_id()


@pytest.fixture
def temp_audit_log(tmp_path):
    """Create a temporary audit log file."""
    audit_file = tmp_path / "audit.log"
    return audit_file
