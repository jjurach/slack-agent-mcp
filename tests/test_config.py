"""
Tests for configuration management.
"""

import os
import tempfile
from pathlib import Path

import pytest

from slack_notifications.config import SlackConfig
from slack_notifications.exceptions import SlackConfigError


class TestSlackConfig:
    """Test SlackConfig class functionality."""

    def test_valid_config_creation(self):
        """Test creating a valid configuration."""
        config = SlackConfig(
            bot_token="xoxb-valid-token-123",
            default_channel="#test",
            timeout=60,
            max_retries=5
        )

        assert config.bot_token == "xoxb-valid-token-123"
        assert config.default_channel == "#test"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_invalid_bot_token(self):
        """Test validation of bot token format."""
        with pytest.raises(ValueError, match="Bot token must start with 'xoxb-'"):
            SlackConfig(bot_token="invalid-token")

        with pytest.raises(ValueError, match="Bot token appears to be too short"):
            SlackConfig(bot_token="xoxb-short")

    def test_invalid_channel(self):
        """Test validation of channel format."""
        with pytest.raises(ValueError, match="Channel must start with"):
            SlackConfig(bot_token="xoxb-valid-token", default_channel="invalid")

    def test_config_validation_limits(self):
        """Test configuration value limits."""
        # Test timeout limits
        with pytest.raises(ValueError):
            SlackConfig(bot_token="xoxb-valid-token", timeout=0)

        with pytest.raises(ValueError):
            SlackConfig(bot_token="xoxb-valid-token", timeout=400)

        # Test max_retries limits
        with pytest.raises(ValueError):
            SlackConfig(bot_token="xoxb-valid-token", max_retries=-1)

        with pytest.raises(ValueError):
            SlackConfig(bot_token="xoxb-valid-token", max_retries=15)

    @pytest.fixture
    def temp_env(self):
        """Fixture to temporarily set environment variables."""
        original_env = dict(os.environ)
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_from_env_success(self, temp_env):
        """Test loading configuration from environment variables."""
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-env-token-123"
        os.environ["SLACK_DEFAULT_CHANNEL"] = "#env-channel"
        os.environ["SLACK_TIMEOUT"] = "45"
        os.environ["SLACK_MAX_RETRIES"] = "2"

        config = SlackConfig.from_env()

        assert config.bot_token == "xoxb-env-token-123"
        assert config.default_channel == "#env-channel"
        assert config.timeout == 45
        assert config.max_retries == 2

    def test_from_env_defaults(self, temp_env):
        """Test environment loading with defaults."""
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-minimal-token"

        config = SlackConfig.from_env()

        assert config.bot_token == "xoxb-minimal-token"
        assert config.default_channel == "#general"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_from_env_missing_token(self, temp_env):
        """Test error when bot token is missing from environment."""
        with pytest.raises(ValueError):
            SlackConfig.from_env()

    def test_from_toml_success(self):
        """Test loading configuration from TOML file."""
        toml_content = """
        [slack]
        bot_token = "xoxb-toml-token-123"
        default_channel = "#toml-channel"
        timeout = 50
        max_retries = 4
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()

            try:
                config = SlackConfig.from_toml(f.name)

                assert config.bot_token == "xoxb-toml-token-123"
                assert config.default_channel == "#toml-channel"
                assert config.timeout == 50
                assert config.max_retries == 4
            finally:
                Path(f.name).unlink()

    def test_from_toml_missing_file(self):
        """Test error when TOML file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            SlackConfig.from_toml("nonexistent.toml")

    def test_from_toml_invalid_content(self):
        """Test error when TOML file has invalid content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("invalid toml content {{{")
            f.flush()

            try:
                with pytest.raises(ValueError):
                    SlackConfig.from_toml(f.name)
            finally:
                Path(f.name).unlink()

    def test_from_toml_missing_slack_section(self):
        """Test error when TOML file lacks slack section."""
        toml_content = """
        [other]
        setting = "value"
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()

            try:
                with pytest.raises(ValueError, match="No 'slack' section found"):
                    SlackConfig.from_toml(f.name)
            finally:
                Path(f.name).unlink()

    def test_auto_load_priority(self, temp_env):
        """Test that auto_load prioritizes TOML over environment."""
        # Set environment variables
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-env-token"
        os.environ["SLACK_DEFAULT_CHANNEL"] = "#env-channel"

        # Create TOML file
        toml_content = """
        [slack]
        bot_token = "xoxb-toml-token"
        default_channel = "#toml-channel"
        """

        toml_path = Path("slack_notifications.toml")
        original_content = None
        if toml_path.exists():
            original_content = toml_path.read_text()

        try:
            toml_path.write_text(toml_content)

            config = SlackConfig.auto_load()

            # Should use TOML values, not environment
            assert config.bot_token == "xoxb-toml-token"
            assert config.default_channel == "#toml-channel"

        finally:
            if original_content is not None:
                toml_path.write_text(original_content)
            elif toml_path.exists():
                toml_path.unlink()

    def test_auto_load_fallback_to_env(self, temp_env):
        """Test that auto_load falls back to environment when TOML fails."""
        # Set environment variables
        os.environ["SLACK_BOT_TOKEN"] = "xoxb-env-fallback-token"

        config = SlackConfig.auto_load()

        assert config.bot_token == "xoxb-env-fallback-token"
        assert config.default_channel == "#general"