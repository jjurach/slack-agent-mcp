"""
MCP Server for Slack notifications.

This module provides a FastMCP server that exposes tools for AI agents
to send notifications to Slack channels.
"""

import logging
from typing import Optional

from fastmcp import FastMCP

from .config import SlackConfig
from .exceptions import SlackConfigError, SlackNotificationError
from .notifier import SlackNotifier

logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(
    "slack-notifications",
    instructions="Send notifications to Slack channels via MCP protocol"
)


@mcp.tool()
def send_slack_message(
    message: str,
    channel: Optional[str] = None,
    level: str = "info"
) -> str:
    """
    Send a notification message to a Slack channel.

    Args:
        message: The message to send
        channel: Target channel (uses default if not specified)
        level: Message level - "info", "success", "warning", or "error"

    Returns:
        Success message with timestamp and channel info

    Raises:
        SlackConfigError: If Slack is not configured
        SlackNotificationError: If message sending fails
    """
    try:
        # Create notifier (will auto-load config)
        notifier = SlackNotifier()

        # Send the message
        response = notifier.notify(message=message, channel=channel, level=level)

        target_channel = channel or notifier.config.default_channel
        return f"✅ Message sent successfully to {target_channel}"

    except SlackConfigError as e:
        error_msg = f"❌ Slack configuration error: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except SlackNotificationError as e:
        error_msg = f"❌ Failed to send Slack message: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"❌ Unexpected error sending Slack message: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


@mcp.tool()
def send_slack_success(
    message: str,
    channel: Optional[str] = None
) -> str:
    """
    Send a success notification to a Slack channel.

    Args:
        message: The success message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Success message with timestamp and channel info
    """
    return send_slack_message(message, channel, "success")


@mcp.tool()
def send_slack_warning(
    message: str,
    channel: Optional[str] = None
) -> str:
    """
    Send a warning notification to a Slack channel.

    Args:
        message: The warning message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Success message with timestamp and channel info
    """
    return send_slack_message(message, channel, "warning")


@mcp.tool()
def send_slack_error(
    message: str,
    channel: Optional[str] = None
) -> str:
    """
    Send an error notification to a Slack channel.

    Args:
        message: The error message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Success message with timestamp and channel info
    """
    return send_slack_message(message, channel, "error")


@mcp.tool()
def configure_slack_notifications(
    bot_token: Optional[str] = None,
    default_channel: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None
) -> str:
    """
    Configure Slack notifications globally.

    Args:
        bot_token: Slack bot token
        default_channel: Default channel for notifications
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Configuration success message
    """
    try:
        from .notifier import configure
        configure(
            bot_token=bot_token,
            default_channel=default_channel,
            timeout=timeout,
            max_retries=max_retries
        )
        return "✅ Slack notifications configured successfully"
    except SlackConfigError as e:
        error_msg = f"❌ Configuration failed: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"❌ Unexpected error during configuration: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


def main():
    """Run the Slack MCP server."""
    logger.info("Starting Slack MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()