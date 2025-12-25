#!/usr/bin/env python3
"""
Slack Agent Script.

This script monitors Slack channels using the Web API and responds
to messages. It specifically handles "what time is it?" queries by responding
with the current time in Central Standard Time (CST).

All interactions are logged to stdout with timestamps.

Usage:
    python slack_agent.py

Configuration:
    The script loads configuration from environment variables. You can set these
    directly or create a .env file in the project root (see .env.example).

Environment Variables:
    SLACK_BOT_TOKEN: Your Slack bot token (required)
    SLACK_AGENT_CHANNELS: Comma-separated list of channel IDs to monitor (optional, default: general channels)
    SLACK_AGENT_POLL_INTERVAL: Polling interval in seconds (optional, default: 5)

The script runs in foreground and polls for new messages periodically.
"""

import logging
import sys
import time
from datetime import datetime
from typing import List, Optional

import pytz
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # Override any existing handlers
)

logger = logging.getLogger(__name__)

# Central Time timezone
CST = pytz.timezone('America/Chicago')


class SlackAgent:
    """
    Slack Web API agent that responds to time queries.

    Monitors Slack channels using Web API polling and responds to messages containing
    "what time is it?" (case insensitive).
    """

    def __init__(self, token: str, channels: Optional[List[str]] = None, poll_interval: int = 5):
        """
        Initialize the Slack agent.

        Args:
            token: Slack bot token
            channels: List of channel IDs to monitor (optional)
            poll_interval: Polling interval in seconds (default: 5)
        """
        self.token = token
        self.web_client = WebClient(token=token)
        self.channels = channels or []
        self.poll_interval = poll_interval

        # Track last seen message timestamps for each channel to avoid duplicates
        self.last_timestamps = {}

        # Bot user ID (will be set during start)
        self.bot_user_id = None

    def _get_channels_to_monitor(self) -> List[str]:
        """
        Get the list of channels to monitor.

        If no channels specified, try to find general-like channels.

        Returns:
            List of channel IDs
        """
        if self.channels:
            return self.channels

        try:
            # Get list of channels the bot can access
            response = self.web_client.conversations_list(types="public_channel,private_channel")

            if response["ok"]:
                channels = response["channels"]
                # Prefer channels with "general" in the name, or just take the first few
                general_channels = [ch for ch in channels if "general" in ch["name"].lower()]
                if general_channels:
                    return [ch["id"] for ch in general_channels[:3]]  # Limit to 3 channels

                # Fallback: take first 3 channels
                return [ch["id"] for ch in channels[:3]]
            else:
                logger.warning("Could not retrieve channel list, will monitor no channels")
                return []

        except SlackApiError as e:
            logger.error(f"Error getting channels: {e.response.get('error', 'unknown')}")
            return []

    def _get_bot_user_id(self) -> Optional[str]:
        """
        Get the bot's user ID.

        Returns:
            Bot user ID or None if error
        """
        try:
            response = self.web_client.auth_test()
            if response["ok"]:
                return response["user_id"]
            else:
                logger.error("Could not authenticate bot")
                return None
        except SlackApiError as e:
            logger.error(f"Error authenticating bot: {e.response.get('error', 'unknown')}")
            return None

    def _is_time_query(self, message_text: str) -> bool:
        """
        Check if the message is asking for the current time.

        Args:
            message_text: The message text to check

        Returns:
            True if this appears to be a time query
        """
        # Convert to lowercase for case-insensitive matching
        message_text = message_text.lower().strip()

        # Exact matches for time queries
        time_queries = [
            "what time is it",
            "what time is it?",
            "what's the time",
            "what's the time?",
            "what is the time",
            "what is the time?",
            "time",
            "current time"
        ]

        return message_text in time_queries

    def _respond_with_time(self, channel: str):
        """
        Respond to a time query with the current CST time.

        Args:
            channel: The channel to respond in
        """
        try:
            # Get current time in CST
            now = datetime.now(CST)
            time_str = now.strftime('%I:%M:%S %p %Z on %Y-%m-%d')

            # Format response
            response = f"The current time is {time_str}"

            # Send response
            result = self.web_client.chat_postMessage(
                channel=channel,
                text=response
            )

            # Log the response
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.info(f"[{log_timestamp}] RESPONSE - Sent time to channel {channel}: {response}")

        except Exception as e:
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.error(f"[{log_timestamp}] Error sending time response to {channel}: {e}")

    def _poll_messages(self):
        """
        Poll channels for new messages and process them.
        """
        channels_to_monitor = self._get_channels_to_monitor()

        if not channels_to_monitor:
            logger.warning("No channels to monitor")
            return

        logger.info(f"Monitoring channels: {', '.join(channels_to_monitor)}")

        for channel_id in channels_to_monitor:
            try:
                # Get recent messages from this channel
                response = self.web_client.conversations_history(
                    channel=channel_id,
                    limit=10,  # Get last 10 messages
                    oldest=self.last_timestamps.get(channel_id, None)
                )

                if response["ok"]:
                    messages = response.get("messages", [])

                    # Process messages in chronological order (oldest first)
                    for message in reversed(messages):
                        message_ts = message.get("ts")
                        user_id = message.get("user")
                        text = message.get("text", "").strip()

                        # Skip messages from the bot itself
                        if user_id == self.bot_user_id:
                            continue

                        # Skip if we've already processed this message
                        if self.last_timestamps.get(channel_id) and message_ts <= self.last_timestamps[channel_id]:
                            continue

                        # Log the incoming message
                        log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
                        logger.info(f"[{log_timestamp}] MESSAGE - Channel: {channel_id}, User: {user_id}, Text: '{message.get('text', '')}'")

                        # Check if this is a time query
                        if self._is_time_query(text):
                            self._respond_with_time(channel_id)

                        # Update last seen timestamp
                        self.last_timestamps[channel_id] = message_ts

                else:
                    logger.warning(f"Failed to get history for channel {channel_id}: {response.get('error', 'unknown')}")

            except SlackApiError as e:
                error_type = e.response.get("error", "unknown") if e.response else "unknown"
                logger.error(f"Error polling channel {channel_id}: {error_type}")
            except Exception as e:
                logger.error(f"Unexpected error polling channel {channel_id}: {e}")

    def start(self):
        """Start the polling loop and begin monitoring messages."""
        log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"[{log_timestamp}] Starting Slack Agent...")

        # Get bot user ID
        self.bot_user_id = self._get_bot_user_id()
        if not self.bot_user_id:
            raise Exception("Could not authenticate bot user")

        logger.info(f"Bot authenticated as user: {self.bot_user_id}")

        try:
            while True:
                self._poll_messages()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.info(f"[{log_timestamp}] Slack Agent stopped by user")
        except Exception as e:
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.error(f"[{log_timestamp}] Error in Slack Agent: {e}")
            raise


def main():
    """Main entry point for the Slack agent script."""
    import os

    # Load environment variables from .env file if it exists
    load_dotenv()

    # Get bot token from environment
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN environment variable is required")
        sys.exit(1)

    # Get channels to monitor from environment
    channels_str = os.getenv("SLACK_AGENT_CHANNELS", "")
    channels = [ch.strip() for ch in channels_str.split(",") if ch.strip()] if channels_str else None

    # Get polling interval from environment
    poll_interval_str = os.getenv("SLACK_AGENT_POLL_INTERVAL", "5")
    try:
        poll_interval = int(poll_interval_str)
        if poll_interval < 1:
            poll_interval = 5
    except ValueError:
        poll_interval = 5

    # Create and start the agent
    agent = SlackAgent(token, channels=channels, poll_interval=poll_interval)
    agent.start()


if __name__ == "__main__":
    main()