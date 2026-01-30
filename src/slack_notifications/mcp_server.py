"""
MCP Server for Slack notifications.

This module provides a FastMCP server that exposes tools for AI agents
to send notifications to Slack channels.
"""

import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .config import SlackConfig
from .exceptions import SlackConfigError, SlackNotificationError
from .logging import configure_logging, get_audit_logger
from .notifier import SlackNotifier
from .utils import clear_request_id, get_request_id, mask_credentials, set_request_id

# Configure logging
configure_logging()
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
) -> Dict[str, Any]:
    """
    Send a notification message to a Slack channel.

    Args:
        message: The message to send
        channel: Target channel (uses default if not specified)
        level: Message level - "info", "success", "warning", or "error"

    Returns:
        Structured response with status, data, and request_id
    """
    request_id = set_request_id()
    audit_logger = get_audit_logger()
    start_time = audit_logger.start_timer()

    try:
        # Create notifier (will auto-load config)
        notifier = SlackNotifier()

        # Send the message
        response = notifier.notify(message=message, channel=channel, level=level)

        target_channel = channel or notifier.config.default_channel
        duration_ms = audit_logger.stop_timer(start_time)

        # Log success
        audit_logger.log_tool_call(
            tool_name="send_slack_message",
            parameters={"message": message, "channel": channel, "level": level},
            request_id=request_id,
            success=True,
            duration_ms=duration_ms,
        )

        return {
            "status": "success",
            "data": {
                "message": f"Message sent successfully to {target_channel}",
                "channel": target_channel,
                "timestamp": response.get("ts"),
            },
            "request_id": request_id,
        }

    except (SlackConfigError, SlackNotificationError) as e:
        error_msg = mask_credentials(str(e))
        duration_ms = audit_logger.stop_timer(start_time)

        # Log failure
        audit_logger.log_tool_call(
            tool_name="send_slack_message",
            parameters={"message": message, "channel": channel, "level": level},
            request_id=request_id,
            success=False,
            error_message=error_msg,
            duration_ms=duration_ms,
        )

        logger.error(f"Failed to send Slack message: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id,
        }

    except Exception as e:
        error_msg = mask_credentials(str(e))
        duration_ms = audit_logger.stop_timer(start_time)

        # Log failure
        audit_logger.log_tool_call(
            tool_name="send_slack_message",
            parameters={"message": message, "channel": channel, "level": level},
            request_id=request_id,
            success=False,
            error_message=error_msg,
            duration_ms=duration_ms,
        )

        logger.error(f"Unexpected error: {error_msg}")
        return {
            "status": "error",
            "message": f"Unexpected error: {error_msg}",
            "request_id": request_id,
        }

    finally:
        clear_request_id()


@mcp.tool()
def send_slack_success(
    message: str,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a success notification to a Slack channel.

    Args:
        message: The success message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Structured response with status, data, and request_id
    """
    return send_slack_message(message, channel, "success")


@mcp.tool()
def send_slack_warning(
    message: str,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a warning notification to a Slack channel.

    Args:
        message: The warning message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Structured response with status, data, and request_id
    """
    return send_slack_message(message, channel, "warning")


@mcp.tool()
def send_slack_error(
    message: str,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an error notification to a Slack channel.

    Args:
        message: The error message to send
        channel: Target channel (uses default if not specified)

    Returns:
        Structured response with status, data, and request_id
    """
    return send_slack_message(message, channel, "error")


@mcp.tool()
def configure_slack_notifications(
    bot_token: Optional[str] = None,
    default_channel: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None
) -> Dict[str, Any]:
    """
    Configure Slack notifications globally.

    Args:
        bot_token: Slack bot token
        default_channel: Default channel for notifications
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Structured response with status, message, and request_id
    """
    request_id = set_request_id()
    audit_logger = get_audit_logger()
    start_time = audit_logger.start_timer()

    try:
        from .notifier import configure
        configure(
            bot_token=bot_token,
            default_channel=default_channel,
            timeout=timeout,
            max_retries=max_retries
        )

        duration_ms = audit_logger.stop_timer(start_time)

        # Log success
        audit_logger.log_tool_call(
            tool_name="configure_slack_notifications",
            parameters={
                "default_channel": default_channel,
                "timeout": timeout,
                "max_retries": max_retries,
            },
            request_id=request_id,
            success=True,
            duration_ms=duration_ms,
        )

        return {
            "status": "success",
            "message": "Slack notifications configured successfully",
            "request_id": request_id,
        }

    except SlackConfigError as e:
        error_msg = mask_credentials(str(e))
        duration_ms = audit_logger.stop_timer(start_time)

        # Log failure
        audit_logger.log_tool_call(
            tool_name="configure_slack_notifications",
            parameters={
                "default_channel": default_channel,
                "timeout": timeout,
                "max_retries": max_retries,
            },
            request_id=request_id,
            success=False,
            error_message=error_msg,
            duration_ms=duration_ms,
        )

        logger.error(f"Configuration failed: {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id,
        }

    except Exception as e:
        error_msg = mask_credentials(str(e))
        duration_ms = audit_logger.stop_timer(start_time)

        # Log failure
        audit_logger.log_tool_call(
            tool_name="configure_slack_notifications",
            parameters={
                "default_channel": default_channel,
                "timeout": timeout,
                "max_retries": max_retries,
            },
            request_id=request_id,
            success=False,
            error_message=error_msg,
            duration_ms=duration_ms,
        )

        logger.error(f"Unexpected error during configuration: {error_msg}")
        return {
            "status": "error",
            "message": f"Unexpected error: {error_msg}",
            "request_id": request_id,
        }

    finally:
        clear_request_id()


def main():
    """Run the Slack MCP server."""
    logger.info("Starting Slack MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()