"""
Unit tests for configuration module.
"""

import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from slack_notifications.config import AppConfig, ProfileConfig, SlackConfig


class TestProfileConfig:
    """Tests for ProfileConfig."""

    def test_valid_profile_config(self):
        """Test valid profile configuration."""
        config = ProfileConfig(
            bot_token_env="SLACK_BOT_TOKEN",
            default_channel="#general",
            timeout=30,
            max_retries=3,
        )
        assert config.bot_token_env == "SLACK_BOT_TOKEN"
        assert config.default_channel == "#general"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_channel_validation(self):
        """Test channel format validation."""
        # Valid channels
        ProfileConfig(bot_token_env="TEST", default_channel="#test")
        ProfileConfig(bot_token_env="TEST", default_channel="@user")

        # Invalid channel
        with pytest.raises(ValidationError):
            ProfileConfig(bot_token_env="TEST", default_channel="invalid")

    def test_timeout_validation(self):
        """Test timeout range validation."""
        # Valid timeout
        ProfileConfig(bot_token_env="TEST", default_channel="#test", timeout=30)

        # Too low
        with pytest.raises(ValidationError):
            ProfileConfig(bot_token_env="TEST", default_channel="#test", timeout=0)

        # Too high
        with pytest.raises(ValidationError):
            ProfileConfig(bot_token_env="TEST", default_channel="#test", timeout=500)

    def test_get_bot_token(self, monkeypatch):
        """Test retrieving bot token from environment."""
        monkeypatch.setenv("TEST_TOKEN", "xoxb-123-456-789")

        config = ProfileConfig(bot_token_env="TEST_TOKEN", default_channel="#test")
        token = config.get_bot_token()

        assert token == "xoxb-123-456-789"

    def test_get_bot_token_missing(self):
        """Test error when token environment variable not set."""
        config = ProfileConfig(bot_token_env="NONEXISTENT_TOKEN", default_channel="#test")

        with pytest.raises(ValueError, match="not found"):
            config.get_bot_token()

    def test_get_bot_token_invalid_format(self, monkeypatch):
        """Test error when token has invalid format."""
        monkeypatch.setenv("BAD_TOKEN", "invalid-token")

        config = ProfileConfig(bot_token_env="BAD_TOKEN", default_channel="#test")

        with pytest.raises(ValueError, match="must start with"):
            config.get_bot_token()


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_app_config(self):
        """Test default app configuration."""
        config = AppConfig()

        assert "default" in config.profiles
        assert config.profiles["default"].bot_token_env == "SLACK_BOT_TOKEN"

    def test_at_least_one_profile(self):
        """Test validation requires at least one profile."""
        with pytest.raises(ValidationError, match="at least one profile"):
            AppConfig(profiles={})

    def test_from_json_file(self, temp_config_dir):
        """Test loading from JSON file."""
        config_file = temp_config_dir / "config.json"

        config_data = {
            "profiles": {
                "work": {
                    "bot_token_env": "SLACK_WORK_TOKEN",
                    "default_channel": "#work",
                    "timeout": 60,
                    "max_retries": 5,
                }
            }
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = AppConfig.from_json_file(config_file)

        assert "work" in config.profiles
        assert config.profiles["work"].bot_token_env == "SLACK_WORK_TOKEN"
        assert config.profiles["work"].default_channel == "#work"


class TestSlackConfig:
    """Tests for SlackConfig."""

    def test_valid_slack_config(self):
        """Test valid Slack configuration."""
        config = SlackConfig(
            bot_token="xoxb-123-456-789",
            default_channel="#general",
            timeout=30,
            max_retries=3,
        )

        assert config.bot_token == "xoxb-123-456-789"
        assert config.default_channel == "#general"

    def test_bot_token_validation(self):
        """Test bot token format validation."""
        # Valid token
        SlackConfig(bot_token="xoxb-123-456-789", default_channel="#test")

        # Invalid prefix
        with pytest.raises(ValidationError, match="must start with"):
            SlackConfig(bot_token="invalid-token", default_channel="#test")

        # Too short
        with pytest.raises(ValidationError, match="too short"):
            SlackConfig(bot_token="xoxb-123", default_channel="#test")

    def test_from_env(self, mock_env_vars):
        """Test loading from environment variables."""
        config = SlackConfig.from_env()

        assert config.bot_token == "xoxb-test-token-1234567890"
        assert config.default_channel == "#test"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_from_profile(self, temp_config_dir, monkeypatch):
        """Test loading from profile."""
        # Set up environment
        monkeypatch.setenv("SLACK_TEST_TOKEN", "xoxb-profile-test-token")

        # Create config file
        config_file = temp_config_dir / "config.json"
        config_data = {
            "profiles": {
                "test": {
                    "bot_token_env": "SLACK_TEST_TOKEN",
                    "default_channel": "#testing",
                    "timeout": 45,
                    "max_retries": 2,
                }
            }
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Override config path
        monkeypatch.setenv("SLACK_AGENT_CONFIG", str(config_file))

        # Load profile
        config = SlackConfig.from_profile("test")

        assert config.bot_token == "xoxb-profile-test-token"
        assert config.default_channel == "#testing"
        assert config.timeout == 45
        assert config.max_retries == 2
