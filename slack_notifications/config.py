"""
Configuration management for Slack notifications.

This module handles configuration loading from environment variables,
config files, and provides validation using Pydantic.
"""

import os
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        tomllib = None

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class SlackConfig(BaseModel):
    """
    Configuration for Slack notifications.

    Supports loading from:
    - Environment variables
    - .env files
    - TOML config files
    """

    bot_token: str = Field(..., description="Slack bot token")
    default_channel: str = Field("#general", description="Default Slack channel")
    timeout: int = Field(30, description="Request timeout in seconds", ge=1, le=300)
    max_retries: int = Field(3, description="Maximum retry attempts", ge=0, le=10)

    @validator("bot_token")
    def validate_bot_token(cls, v):
        """Validate that the bot token has the correct format."""
        if not v.startswith("xoxb-"):
            raise ValueError("Bot token must start with 'xoxb-'")
        if len(v) < 20:
            raise ValueError("Bot token appears to be too short")
        return v

    @validator("default_channel")
    def validate_channel(cls, v):
        """Validate channel format."""
        if not v.startswith(("#", "@")):
            raise ValueError("Channel must start with '#' or '@'")
        return v

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """
        Load configuration from environment variables.

        Environment variables:
        - SLACK_BOT_TOKEN (required)
        - SLACK_DEFAULT_CHANNEL (optional, default: "#general")
        - SLACK_TIMEOUT (optional, default: 30)
        - SLACK_MAX_RETRIES (optional, default: 3)
        """
        # Load .env file if it exists
        load_dotenv()

        return cls(
            bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
            default_channel=os.getenv("SLACK_DEFAULT_CHANNEL", "#general"),
            timeout=int(os.getenv("SLACK_TIMEOUT", "30")),
            max_retries=int(os.getenv("SLACK_MAX_RETRIES", "3")),
        )

    @classmethod
    def from_toml(cls, path: Optional[str] = None) -> "SlackConfig":
        """
        Load configuration from a TOML file.

        Args:
            path: Path to TOML file. If None, looks for 'slack_notifications.toml'

        Returns:
            SlackConfig instance

        Raises:
            FileNotFoundError: If TOML file doesn't exist
            ImportError: If tomllib/tomli is not available
            ValueError: If TOML parsing fails
        """
        if tomllib is None:
            raise ImportError(
                "TOML support requires 'tomli' for Python < 3.11 or built-in tomllib for Python >= 3.11"
            )

        if path is None:
            path = "slack_notifications.toml"

        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse TOML config: {e}")

        # Extract slack section
        slack_config = data.get("slack", {})
        if not slack_config:
            raise ValueError("No 'slack' section found in TOML config")

        return cls(**slack_config)

    @classmethod
    def auto_load(cls) -> "SlackConfig":
        """
        Automatically load configuration in order of priority:
        1. TOML file (slack_notifications.toml)
        2. Environment variables (including .env)

        Returns:
            SlackConfig instance

        Raises:
            ValueError: If no valid configuration found
        """
        # Try TOML first
        try:
            return cls.from_toml()
        except (FileNotFoundError, ImportError, ValueError):
            pass

        # Fall back to environment
        try:
            return cls.from_env()
        except Exception as e:
            raise ValueError(
                "No valid Slack configuration found. "
                "Please set environment variables or create slack_notifications.toml. "
                f"Error: {e}"
            ) from e