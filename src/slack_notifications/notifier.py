"""
High-level notification API for Slack notifications.

This module provides the main user-facing API for sending notifications
to Slack channels at application milestones.
"""

import asyncio
import logging
from typing import Optional, Union

from .client import SlackClient
from .config import SlackConfig
from .exceptions import SlackConfigError, SlackNotificationError

logger = logging.getLogger(__name__)

# Global configuration instance
_global_config: Optional[SlackConfig] = None
_global_client: Optional[SlackClient] = None


def _get_global_client() -> SlackClient:
    """Get or create the global Slack client instance."""
    global _global_config, _global_client

    if _global_client is None:
        if _global_config is None:
            try:
                _global_config = SlackConfig.auto_load()
            except Exception as e:
                raise SlackConfigError(
                    "No Slack configuration found. Please configure via environment variables, "
                    ".env file, or slack_notifications.toml, or call configure() first."
                ) from e

        _global_client = SlackClient(_global_config)

    return _global_client


def configure(
    bot_token: Optional[str] = None,
    default_channel: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> None:
    """
    Configure the global Slack notification settings.

    Args:
        bot_token: Slack bot token (if not provided, loaded from config)
        default_channel: Default channel (if not provided, loaded from config)
        timeout: Request timeout in seconds (if not provided, loaded from config)
        max_retries: Maximum retry attempts (if not provided, loaded from config)

    Raises:
        SlackConfigError: If configuration is invalid
    """
    global _global_config, _global_client

    try:
        if bot_token or default_channel or timeout is not None or max_retries is not None:
            # Custom configuration provided
            config_dict = {}
            if bot_token:
                config_dict["bot_token"] = bot_token
            if default_channel:
                config_dict["default_channel"] = default_channel
            if timeout is not None:
                config_dict["timeout"] = timeout
            if max_retries is not None:
                config_dict["max_retries"] = max_retries

            _global_config = SlackConfig(**config_dict)
        else:
            # Load from environment/config files
            _global_config = SlackConfig.auto_load()

        # Reset client to use new config
        _global_client = SlackClient(_global_config)
        logger.info("Slack notifications configured successfully")

    except Exception as e:
        raise SlackConfigError(f"Failed to configure Slack notifications: {e}") from e


class SlackNotifier:
    """
    High-level Slack notification manager.

    Provides methods for sending various types of notifications
    with proper formatting and error handling.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        default_channel: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize the Slack notifier.

        Args:
            bot_token: Slack bot token
            default_channel: Default channel for notifications
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        config_dict = {}
        if bot_token:
            config_dict["bot_token"] = bot_token
        if default_channel:
            config_dict["default_channel"] = default_channel
        if timeout is not None:
            config_dict["timeout"] = timeout
        if max_retries is not None:
            config_dict["max_retries"] = max_retries

        if config_dict:
            self.config = SlackConfig(**config_dict)
        else:
            self.config = SlackConfig.auto_load()

        self.client = SlackClient(self.config)

    def notify(
        self,
        message: str,
        channel: Optional[str] = None,
        level: str = "info",
        **kwargs
    ) -> dict:
        """
        Send a notification to Slack.

        Args:
            message: The notification message
            channel: Target channel (uses default if not specified)
            level: Message level ("info", "success", "warning", "error")
            **kwargs: Additional arguments for Slack API

        Returns:
            Slack API response

        Raises:
            SlackNotificationError: If notification fails
        """
        target_channel = channel or self.config.default_channel
        formatted_message = self._format_message(message, level)

        logger.debug(f"Sending {level} notification to {target_channel}: {message}")

        try:
            response = self.client.post_message(
                channel=target_channel,
                text=formatted_message,
                **kwargs
            )
            logger.info(f"Notification sent successfully to {target_channel}")
            return response
        except Exception as e:
            logger.error(f"Failed to send notification to {target_channel}: {e}")
            raise

    async def notify_async(
        self,
        message: str,
        channel: Optional[str] = None,
        level: str = "info",
        **kwargs
    ) -> dict:
        """
        Send a notification to Slack asynchronously.

        Args:
            message: The notification message
            channel: Target channel (uses default if not specified)
            level: Message level ("info", "success", "warning", "error")
            **kwargs: Additional arguments for Slack API

        Returns:
            Slack API response

        Raises:
            SlackNotificationError: If notification fails
        """
        target_channel = channel or self.config.default_channel
        formatted_message = self._format_message(message, level)

        logger.debug(f"Sending {level} notification async to {target_channel}: {message}")

        try:
            response = await self.client.post_message_async(
                channel=target_channel,
                text=formatted_message,
                **kwargs
            )
            logger.info(f"Async notification sent successfully to {target_channel}")
            return response
        except Exception as e:
            logger.error(f"Failed to send async notification to {target_channel}: {e}")
            raise

    def _format_message(self, message: str, level: str) -> str:
        """
        Format a message based on its level.

        Args:
            message: The raw message
            level: Message level

        Returns:
            Formatted message with appropriate emoji
        """
        emojis = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }

        emoji = emojis.get(level, "📢")
        return f"{emoji} {message}"


# Convenience functions for global usage

def notify_milestone(
    message: str,
    channel: Optional[str] = None,
    level: str = "info",
    **kwargs
) -> dict:
    """
    Send a milestone notification using global configuration.

    This is a convenience function that uses the globally configured
    Slack client. Call configure() first or set environment variables.

    Args:
        message: The milestone message
        channel: Target channel (uses configured default if not specified)
        level: Message level ("info", "success", "warning", "error")
        **kwargs: Additional arguments for Slack API

    Returns:
        Slack API response

    Raises:
        SlackConfigError: If not configured
        SlackNotificationError: If notification fails
    """
    client = _get_global_client()
    notifier = SlackNotifier()
    notifier.client = client
    notifier.config = _global_config
    return notifier.notify(message, channel, level, **kwargs)


async def notify_milestone_async(
    message: str,
    channel: Optional[str] = None,
    level: str = "info",
    **kwargs
) -> dict:
    """
    Send a milestone notification asynchronously using global configuration.

    This is a convenience function that uses the globally configured
    Slack client. Call configure() first or set environment variables.

    Args:
        message: The milestone message
        channel: Target channel (uses configured default if not specified)
        level: Message level ("info", "success", "warning", "error")
        **kwargs: Additional arguments for Slack API

    Returns:
        Slack API response

    Raises:
        SlackConfigError: If not configured
        SlackNotificationError: If notification fails
    """
    client = _get_global_client()
    notifier = SlackNotifier()
    notifier.client = client
    notifier.config = _global_config
    return await notifier.notify_async(message, channel, level, **kwargs)