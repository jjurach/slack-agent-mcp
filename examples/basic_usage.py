#!/usr/bin/env python3
"""
Basic usage example for slack-notifications.

This script demonstrates the simplest way to use the library
to send notifications to Slack.
"""

import os
from slack_notifications import notify_milestone, SlackNotifier

def main():
    """Demonstrate basic notification usage."""

    # Method 1: Using convenience function with environment variables
    print("=== Method 1: Convenience Function ===")

    # Make sure you have these environment variables set:
    # export SLACK_BOT_TOKEN="xoxb-your-bot-token"
    # export SLACK_DEFAULT_CHANNEL="#general"

    try:
        # Send a simple milestone notification
        response = notify_milestone("Application started successfully!")
        print(f"✅ Notification sent! Response: {response.get('ok', False)}")

        # Send different types of notifications
        notify_milestone("Database migration completed", level="success")
        notify_milestone("Warning: High memory usage detected", level="warning")
        notify_milestone("Error occurred during processing", level="error")

        # Send to specific channel
        notify_milestone("Deploy completed", channel="#deployments", level="success")

    except Exception as e:
        print(f"❌ Failed to send notification: {e}")

    print("\n=== Method 2: Using SlackNotifier Class ===")

    # Method 2: Using the SlackNotifier class directly
    try:
        # Create notifier with explicit configuration
        notifier = SlackNotifier(
            bot_token=os.getenv("SLACK_BOT_TOKEN"),
            default_channel="#notifications"
        )

        # Send notifications using the class
        notifier.notify("Custom notification via class", level="info")
        notifier.notify("Another notification", channel="#random", level="success")

        print("✅ Class-based notifications sent successfully!")

    except Exception as e:
        print(f"❌ Failed to send class-based notification: {e}")

    print("\n=== Configuration Examples ===")

    # Show configuration options
    print("To configure the library, you can:")
    print("1. Set environment variables:")
    print("   export SLACK_BOT_TOKEN='xoxb-your-token'")
    print("   export SLACK_DEFAULT_CHANNEL='#general'")
    print("   export SLACK_TIMEOUT='30'")
    print("   export SLACK_MAX_RETRIES='3'")
    print()
    print("2. Create a .env file with the same variables")
    print()
    print("3. Create a slack_notifications.toml file:")
    print("   [slack]")
    print("   bot_token = 'xoxb-your-token'")
    print("   default_channel = '#general'")
    print("   timeout = 30")
    print("   max_retries = 3")
    print()
    print("4. Call configure() in your code:")
    print("   from slack_notifications import configure")
    print("   configure(bot_token='xoxb-your-token', default_channel='#general')")

if __name__ == "__main__":
    main()