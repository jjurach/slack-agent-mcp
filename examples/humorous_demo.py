#!/usr/bin/env python3
"""
Humorous demo script for slack-notifications.

This script sends funny test messages to a configured Slack channel
to demonstrate the notification functionality in an entertaining way.
Perfect for testing your Slack integration with a smile!

Environment Variables Required:
- SLACK_BOT_TOKEN (required): Your Slack bot token (starts with xoxb-)
- SLACK_DEFAULT_CHANNEL (optional): Target channel, defaults to "#general"
- SLACK_TIMEOUT (optional): Request timeout in seconds, defaults to 30
- SLACK_MAX_RETRIES (optional): Maximum retry attempts, defaults to 3
"""

import os
import time
import random
from slack_notifications import notify_milestone, SlackNotificationError

# Collection of humorous test messages
HUMOROUS_MESSAGES = [
    # Tech puns and jokes
    ("🤖 Bot successfully initialized. Beep boop, I'm not plotting world domination... yet!", "success"),
    ("💾 Loading humor module... 404: Dad jokes not found. Using tech puns instead!", "info"),
    ("🌐 Connected to the cloud. It's not a silver lining, it's just server vapor.", "success"),
    ("⚡ System running at 110% efficiency. That's 10% more than physically possible!", "warning"),
    ("🔧 Debug mode activated. Found 0 bugs. Clearly, the bugs are too smart for our debugger.", "info"),

    # Programming humor
    ("🐛 Bug hunt successful! The bug was hiding in plain sight, wearing camouflage.", "success"),
    ("📝 Code review completed. It's so clean, it squeaks when you run it!", "success"),
    ("🔄 Infinite loop detected... just kidding! Or am I? 🤔", "warning"),
    ("💻 Compiling coffee... Wait, wrong language. Compiling Python instead.", "info"),
    ("🎯 Test suite passed! Even the flaky tests behaved themselves today.", "success"),

    # DevOps humor
    ("🚀 Deployment successful! The servers are now 0.001% less stable.", "success"),
    ("📊 Monitoring alert: CPU usage at 42%. Don't panic, it's just the answer to everything.", "warning"),
    ("🔄 Auto-scaling triggered. Because who doesn't love surprise infrastructure bills?", "info"),
    ("🛡️ Security scan complete. Found 0 vulnerabilities. Or did we? Suspense!", "success"),
    ("💾 Backup completed. Your data is now safely stored in the cloud... we hope.", "info"),

    # Random fun
    ("🎉 Confetti cannon activated! *throws digital confetti* 🎊", "success"),
    ("🔔 Notification test: If you can read this, the matrix is working properly.", "info"),
    ("🌟 Achievement unlocked: Successfully sent a Slack message!", "success"),
    ("🎪 Welcome to the notification circus! Watch in awe as messages appear!", "info"),
    ("🧪 Experimental feature activated. If this breaks, blame the lab assistant.", "warning"),
]

def validate_environment():
    """Validate required environment variables and show configuration."""
    print("🎭 Slack Humorous Demo - Configuration Check")
    print("=" * 50)

    # Check required bot token
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        print("❌ ERROR: SLACK_BOT_TOKEN environment variable is required!")
        print()
        print("To fix this, run:")
        print("export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'")
        print()
        print("Get your bot token from: https://api.slack.com/apps")
        return False

    if not bot_token.startswith("xoxb-"):
        print("❌ ERROR: Bot token must start with 'xoxb-'")
        return False

    # Show configuration
    channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
    timeout = int(os.getenv("SLACK_TIMEOUT", "30"))
    max_retries = int(os.getenv("SLACK_MAX_RETRIES", "3"))

    print("✅ Configuration loaded:")
    print(f"   Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"   Channel: {channel}")
    print(f"   Timeout: {timeout}s")
    print(f"   Max Retries: {max_retries}")
    print()

    return True

def send_humorous_notifications():
    """Send a series of humorous test notifications."""
    print("🎪 Starting humorous notification demo...")
    print("Sending messages to Slack with dramatic pauses for effect!")
    print()

    # Shuffle messages for variety
    messages_to_send = HUMOROUS_MESSAGES.copy()
    random.shuffle(messages_to_send)

    # Send first 5 messages as a demo
    for i, (message, level) in enumerate(messages_to_send[:5], 1):
        try:
            print(f"📤 Sending message {i}/5: {message[:50]}...")

            response = notify_milestone(message, level=level)
            print(f"   ✅ Sent successfully (level: {level})")

            # Add a fun delay between messages
            if i < 5:
                delay = random.uniform(1.0, 3.0)
                print(f"   ⏳ Waiting {delay:.1f} seconds before next message...")
                time.sleep(delay)

        except SlackNotificationError as e:
            print(f"   ❌ Failed to send: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False

    return True

def demonstrate_error_handling():
    """Demonstrate error handling with a fake error scenario."""
    print()
    print("🎭 Demonstrating error handling...")

    try:
        # This will trigger an error (but we'll catch it)
        notify_milestone("Testing error handling - this should work fine!", level="error")
        print("✅ Error-level notification sent successfully")
    except SlackNotificationError as e:
        print(f"❌ Notification failed: {e}")
        return False

    return True

def main():
    """Run the humorous demo."""
    print("🎭 Welcome to the Slack Notifications Humorous Demo!")
    print("This script will send funny test messages to your Slack channel.")
    print()

    # Validate configuration
    if not validate_environment():
        print("❌ Demo aborted due to configuration issues.")
        print("Please set the required environment variables and try again.")
        return 1

    # Send notifications
    if not send_humorous_notifications():
        print("❌ Demo failed during notification sending.")
        return 1

    # Demonstrate error handling
    if not demonstrate_error_handling():
        print("❌ Demo failed during error handling demonstration.")
        return 1

    print()
    print("🎉 Demo completed successfully!")
    print("Check your Slack channel for the humorous messages.")
    print()
    print("💡 Pro tip: Run this script anytime you want to test your Slack integration")
    print("   with a smile, or impress your coworkers with your notification skills!")
    print()

    return 0

if __name__ == "__main__":
    exit(main())