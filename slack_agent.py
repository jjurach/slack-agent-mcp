#!/usr/bin/env python3
"""
Slack Agent Script.

This script connects to Slack using Real Time Messaging (RTM) and responds
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

The script runs in foreground and processes messages in real-time.
"""

import logging
import sys
import time
from datetime import datetime
from typing import Optional

import pytz
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.rtm_v2 import RTMClient

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
    Slack RTM agent that responds to time queries.

    Connects to Slack via RTM and listens for messages containing
    "what time is it?" (case insensitive).
    """

    def __init__(self, token: str):
        """
        Initialize the Slack agent.

        Args:
            token: Slack bot token
        """
        self.token = token
        self.rtm_client = RTMClient(token=token)
        self.web_client = WebClient(token=token)

        # Set up event handlers
        self.rtm_client.on("message")(self.handle_message)
        self.rtm_client.on("hello")(self.handle_hello)
        self.rtm_client.on("goodbye")(self.handle_goodbye)

    def handle_hello(self, payload):
        """Handle RTM connection established."""
        timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"[{timestamp}] RTM connection established - Hello from Slack!")

    def handle_goodbye(self, payload):
        """Handle RTM disconnection."""
        timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"[{timestamp}] RTM connection closed - Goodbye from Slack!")

    def handle_message(self, payload):
        """
        Handle incoming messages.

        Responds to "what time is it?" queries with current CST time.
        """
        try:
            # Extract message details
            data = payload.get("data", {})
            message_text = data.get("text", "").strip().lower()
            channel = data.get("channel", "")
            user = data.get("user", "")
            timestamp = data.get("ts", "")

            # Log the incoming message
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.info(f"[{log_timestamp}] MESSAGE - Channel: {channel}, User: {user}, Text: '{data.get('text', '')}'")

            # Check if this is a time query
            if self._is_time_query(message_text):
                self._respond_with_time(channel)

        except Exception as e:
            log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.error(f"[{log_timestamp}] Error handling message: {e}")

    def _is_time_query(self, message_text: str) -> bool:
        """
        Check if the message is asking for the current time.

        Args:
            message_text: The message text to check

        Returns:
            True if this appears to be a time query
        """
        time_queries = [
            "what time is it",
            "what's the time",
            "what is the time",
            "what time is it?",
            "what's the time?",
            "what is the time?",
            "time",
            "current time"
        ]

        return any(query in message_text for query in time_queries)

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

    def start(self):
        """Start the RTM connection and begin listening for messages."""
        log_timestamp = datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"[{log_timestamp}] Starting Slack Agent...")

        try:
            self.rtm_client.start()
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

    # Create and start the agent
    agent = SlackAgent(token)
    agent.start()


if __name__ == "__main__":
    main()