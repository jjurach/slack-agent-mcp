"""
Configuration management for Slack notifications.

This module handles configuration loading from environment variables,
config files, and provides validation using Pydantic.

Supports profile-based configuration for managing multiple Slack workspaces.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class ProfileConfig(BaseModel):
    """
    Configuration for a single Slack profile.

    Each profile represents a different Slack workspace or token.
    """

    bot_token_env: str = Field(..., description="Environment variable name for bot token")
    default_channel: str = Field("#general", description="Default Slack channel")
    timeout: int = Field(30, description="Request timeout in seconds", ge=1, le=300)
    max_retries: int = Field(3, description="Maximum retry attempts", ge=0, le=10)

    @validator("default_channel")
    def validate_channel(cls, v):
        """Validate channel format."""
        if not v.startswith(("#", "@")):
            raise ValueError("Channel must start with '#' or '@'")
        return v

    def get_bot_token(self) -> str:
        """
        Get the bot token from the environment variable.

        Returns:
            Bot token value

        Raises:
            ValueError: If token not found or invalid
        """
        token = os.getenv(self.bot_token_env, "")
        if not token:
            raise ValueError(f"Bot token not found in environment variable: {self.bot_token_env}")

        if not token.startswith("xoxb-"):
            raise ValueError(f"Bot token must start with 'xoxb-', got token from {self.bot_token_env}")

        if len(token) < 20:
            raise ValueError(f"Bot token appears to be too short: {self.bot_token_env}")

        return token


class AppConfig(BaseModel):
    """
    Application configuration with profile support.

    Profiles allow managing multiple Slack workspaces or different token configurations.
    """

    profiles: Dict[str, ProfileConfig] = Field(
        default_factory=lambda: {
            "default": ProfileConfig(
                bot_token_env="SLACK_BOT_TOKEN",
                default_channel="#general",
            )
        },
        description="Profile configurations"
    )

    @validator("profiles")
    def at_least_one_profile(cls, v):
        """Validate that at least one profile exists."""
        if not v:
            raise ValueError("At least one profile required")
        return v

    @classmethod
    def from_json_file(cls, path: Optional[Path] = None) -> "AppConfig":
        """
        Load configuration from a JSON file.

        Args:
            path: Path to config.json. If None, uses XDG config location.

        Returns:
            AppConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If JSON parsing fails
        """
        if path is None:
            # XDG compliant config location
            config_dir = Path.home() / ".config" / "slack-agent"
            path = config_dir / "config.json"

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON config: {e}")

        return cls(**data)

    @classmethod
    def from_env_override(cls) -> Optional["AppConfig"]:
        """
        Load configuration from environment variable override.

        Environment variables:
        - SLACK_AGENT_CONFIG: Path to config.json

        Returns:
            AppConfig instance if override set, None otherwise
        """
        config_path_str = os.getenv("SLACK_AGENT_CONFIG")
        if not config_path_str:
            return None

        config_path = Path(config_path_str)
        return cls.from_json_file(config_path)

    @classmethod
    def auto_load(cls) -> "AppConfig":
        """
        Automatically load configuration in order of priority:
        1. SLACK_AGENT_CONFIG environment variable
        2. ~/.config/slack-agent/config.json
        3. Default single-profile configuration from environment

        Returns:
            AppConfig instance
        """
        # Try environment override first
        try:
            config = cls.from_env_override()
            if config:
                return config
        except (FileNotFoundError, ValueError):
            pass

        # Try default config file location
        try:
            return cls.from_json_file()
        except (FileNotFoundError, ValueError):
            pass

        # Fall back to default profile from environment
        return cls()


class SlackConfig(BaseModel):
    """
    Resolved configuration for Slack notifications.

    This is the configuration actually used by the notifier,
    resolved from a profile with the actual bot token.
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
    def from_profile(cls, profile_name: str = "default") -> "SlackConfig":
        """
        Load configuration from a named profile.

        Args:
            profile_name: Name of the profile to load

        Returns:
            SlackConfig instance with resolved token

        Raises:
            ValueError: If profile not found or token invalid
        """
        # Load .env file if it exists
        load_dotenv()

        # Get profile from environment variable override if set
        env_profile = os.getenv("SLACK_AGENT_PROFILE")
        if env_profile:
            profile_name = env_profile

        # Load app config
        app_config = AppConfig.auto_load()

        # Get the profile
        if profile_name not in app_config.profiles:
            raise ValueError(f"Profile '{profile_name}' not found in configuration")

        profile = app_config.profiles[profile_name]

        # Resolve the bot token
        bot_token = profile.get_bot_token()

        # Return resolved config
        return cls(
            bot_token=bot_token,
            default_channel=profile.default_channel,
            timeout=profile.timeout,
            max_retries=profile.max_retries,
        )

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """
        Load configuration from environment variables (legacy method).

        Environment variables:
        - SLACK_BOT_TOKEN (required)
        - SLACK_DEFAULT_CHANNEL (optional, default: "#general")
        - SLACK_TIMEOUT (optional, default: 30)
        - SLACK_MAX_RETRIES (optional, default: 3)

        Returns:
            SlackConfig instance
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
    def auto_load(cls) -> "SlackConfig":
        """
        Automatically load configuration.

        Priority order:
        1. Profile-based configuration (from config.json or environment)
        2. Direct environment variables (legacy)

        Returns:
            SlackConfig instance

        Raises:
            ValueError: If no valid configuration found
        """
        # Try profile-based configuration first
        try:
            return cls.from_profile()
        except (FileNotFoundError, ValueError):
            pass

        # Fall back to direct environment variables
        try:
            return cls.from_env()
        except Exception as e:
            raise ValueError(
                "No valid Slack configuration found. "
                "Please set SLACK_BOT_TOKEN environment variable or create ~/.config/slack-agent/config.json. "
                f"Error: {e}"
            ) from e