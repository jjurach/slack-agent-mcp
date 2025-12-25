#!/usr/bin/env python3
"""
Slack MCP Server Entry Point.

This script runs the FastMCP server for Slack notifications,
allowing AI agents to send messages to Slack channels via MCP protocol.

Usage:
    python slack_mcp_server.py

Environment Variables:
    SLACK_BOT_TOKEN: Your Slack bot token (required)
    SLACK_DEFAULT_CHANNEL: Default channel for notifications (optional, default: "#general")
    SLACK_TIMEOUT: Request timeout in seconds (optional, default: 30)
    SLACK_MAX_RETRIES: Maximum retry attempts (optional, default: 3)

Or create a slack_notifications.toml file with your configuration.
"""

import logging
import sys
from pathlib import Path

# Add the current directory to Python path so we can import slack_notifications
sys.path.insert(0, str(Path(__file__).parent))

from slack_notifications.mcp_server import main

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        main()
    except KeyboardInterrupt:
        print("\nSlack MCP server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Slack MCP server: {e}")
        sys.exit(1)