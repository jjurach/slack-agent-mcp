# Implementation Reference

This document provides practical implementation patterns, code examples, and best practices for the slack-agent project.

## Quick Reference

- **Notification Pattern:** Send a Slack notification - see [Basic Notification Pattern](#basic-notification-pattern)
- **Configuration Pattern:** Load and use configuration - see [Configuration Pattern](#configuration-pattern)
- **Error Handling Pattern:** Handle notification failures - see [Error Handling Pattern](#error-handling-pattern)
- **Async Pattern:** Send async notifications - see [Async Notification Pattern](#async-notification-pattern)
- **MCP Server Pattern:** Expose as MCP tool - see [MCP Server Integration](#mcp-server-integration)
- **RTM Agent Pattern:** Build RTM-based bot - see [RTM Agent Pattern](#rtm-agent-pattern)

## Core Patterns

### Basic Notification Pattern

**Use Case:** Send a simple notification to Slack

**Code:**
```python
from slack_notifications import notify_milestone

# Simple notification (uses default channel and level)
notify_milestone("Application started successfully!")

# Notification with custom channel
notify_milestone("Database migration completed", channel="#dev-ops")

# Notification with custom level
notify_milestone("Critical error occurred", level="error")

# All options
notify_milestone(
    message="Deployment finished",
    channel="#deployments",
    level="success"  # info, success, warning, error
)
```

**Key Points:**
- `notify_milestone()` is the main synchronous API
- Channel defaults to `SLACK_DEFAULT_CHANNEL` if not specified
- Level controls message formatting and emoji
- Raises `SlackNotificationError` on failure

### Configuration Pattern

**Use Case:** Load configuration from multiple sources

**Code:**
```python
from slack_notifications import SlackNotifier
from slack_notifications.config import Config

# Method 1: Using defaults (reads env vars and .env)
notifier = SlackNotifier()

# Method 2: Create custom notifier with explicit config
config = Config(
    bot_token="xoxb-your-token",
    default_channel="#notifications",
    timeout=60,
    max_retries=3
)
notifier = SlackNotifier(config=config)

# Method 3: Create notifier with keyword arguments
notifier = SlackNotifier(
    bot_token="xoxb-your-token",
    default_channel="#alerts"
)

# Access configuration values
channel = notifier.config.default_channel
timeout = notifier.config.timeout
```

**Configuration Priority:**
1. Environment variables (`SLACK_BOT_TOKEN`, `SLACK_DEFAULT_CHANNEL`, etc.)
2. `.env` file (automatically loaded)
3. TOML file (`slack_notifications.toml`)
4. Built-in defaults

**Example .env file:**
```bash
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_DEFAULT_CHANNEL=#notifications
SLACK_TIMEOUT=30
SLACK_MAX_RETRIES=3
```

### Error Handling Pattern

**Use Case:** Gracefully handle notification failures

**Code:**
```python
from slack_notifications import notify_milestone, SlackNotificationError
import logging

logger = logging.getLogger(__name__)

try:
    notify_milestone("Application started", channel="#devops")
    logger.info("Notification sent successfully")
except SlackNotificationError as e:
    logger.error(f"Failed to send notification: {e}")
    # Continue execution - don't fail the whole app
    # Could also: retry, log to file, alert admin, etc.
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle other unexpected errors
```

**Error Handling Strategy:**
- Notifications should be non-blocking
- Always wrap in try-except
- Log failures for debugging
- Continue application execution on failure
- Consider fallback strategies (logging, database, etc.)

### Async Notification Pattern

**Use Case:** Send non-blocking notifications in async applications

**Code:**
```python
import asyncio
from slack_notifications import notify_milestone_async

async def main():
    # Send notification asynchronously
    await notify_milestone_async("Async task completed")

    # Multiple concurrent notifications
    await asyncio.gather(
        notify_milestone_async("Task 1 done", channel="#task1"),
        notify_milestone_async("Task 2 done", channel="#task2"),
        notify_milestone_async("Task 3 done", channel="#task3")
    )

    # Async with error handling
    try:
        await notify_milestone_async("Critical alert", level="error")
    except Exception as e:
        print(f"Error: {e}")

# Run async code
asyncio.run(main())
```

**Key Points:**
- Use `notify_milestone_async()` for async code
- Non-blocking - execution continues immediately
- Can be awaited or fired-and-forgotten
- Suitable for web frameworks (FastAPI, Django async)
- Use `asyncio.gather()` for concurrent notifications

### Logging Integration Pattern

**Use Case:** Automatically send error logs to Slack

**Code:**
```python
import logging
from slack_notifications import SlackHandler

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Add console handler
console = logging.StreamHandler()
logger.addHandler(console)

# Add Slack handler (sends ERROR and CRITICAL to Slack)
slack_handler = SlackHandler(
    channel="#error-logs",
    level=logging.ERROR
)
logger.addHandler(slack_handler)

# Now errors automatically go to Slack
logger.error("This error will appear in Slack!")
logger.critical("This critical message will also appear!")
logger.warning("This warning goes to console only")
```

**Key Points:**
- `SlackHandler` integrates with Python logging module
- Configure level to control which messages are sent
- Separate channels for different severity levels
- Non-blocking logging doesn't slow down application

### Testing Patterns

**Unit Test Pattern:**
```python
import pytest
from unittest.mock import patch, MagicMock
from slack_notifications import SlackNotifier, SlackNotificationError

@pytest.fixture
def notifier():
    return SlackNotifier(
        bot_token="xoxb-test-token",
        default_channel="#test"
    )

def test_notify_success(notifier):
    """Test successful notification"""
    with patch('slack_sdk.WebClient.chat_postMessage') as mock_post:
        mock_post.return_value = {'ok': True, 'ts': '123456'}

        result = notifier.notify("Test message")

        assert result is not None
        mock_post.assert_called_once()

def test_notify_api_error(notifier):
    """Test API error handling"""
    with patch('slack_sdk.WebClient.chat_postMessage') as mock_post:
        mock_post.side_effect = Exception("API Error")

        with pytest.raises(SlackNotificationError):
            notifier.notify("Test message")

def test_config_from_env(monkeypatch):
    """Test configuration from environment"""
    monkeypatch.setenv('SLACK_BOT_TOKEN', 'xoxb-test')
    monkeypatch.setenv('SLACK_DEFAULT_CHANNEL', '#test')

    notifier = SlackNotifier()

    assert notifier.config.bot_token == 'xoxb-test'
    assert notifier.config.default_channel == '#test'
```

**Integration Test Pattern:**
```python
import pytest
import os
from slack_notifications import notify_milestone

@pytest.mark.integration
def test_notification_e2e():
    """Full end-to-end test with real Slack workspace"""
    # Only run if test token is available
    if not os.getenv('SLACK_TEST_BOT_TOKEN'):
        pytest.skip("Test Slack bot token not available")

    # Send real test notification
    notify_milestone(
        "Integration test notification",
        channel="#test",
        level="info"
    )
    # Manual verification: check Slack channel for message
```

## Advanced Patterns

### MCP Server Integration

**Use Case:** Expose slack-notifications as MCP tools for AI agents

**Code:**
```python
# In slack_notifications/mcp_server.py
from fastmcp import FastMCP
from slack_notifications import SlackNotifier

app = FastMCP()
notifier = SlackNotifier()

@app.tool()
def send_slack_message(
    message: str,
    channel: str = None,
    level: str = "info"
) -> str:
    """Send a Slack message via MCP."""
    try:
        notifier.notify(message, channel=channel, level=level)
        return f"Message sent to {channel or 'default channel'}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.tool()
def send_slack_error(message: str, channel: str = None) -> str:
    """Send an error notification to Slack."""
    return send_slack_message(message, channel, level="error")

@app.tool()
def send_slack_success(message: str, channel: str = None) -> str:
    """Send a success notification to Slack."""
    return send_slack_message(message, channel, level="success")

if __name__ == "__main__":
    app.run()
```

**AI Agent Integration Example:**
```
AI Agent: "The deployment completed successfully. Notify the team."

MCP Tool Call: send_slack_success(
    message="🚀 Production deployment v2.1.0 completed successfully!",
    channel="#deployments"
)

Result: "Message sent to #deployments"
```

### RTM Agent Pattern

**Use Case:** Build a real-time Slack bot that responds to messages

**Code:**
```python
# In slack_agent/__main__.py
from slack_sdk.rtm_v2 import RTMClient
from slack_notifications import SlackNotifier
import re
from datetime import datetime
import pytz

class SlackTimeBot:
    def __init__(self, token: str):
        self.client = RTMClient(token=token)
        self.notifier = SlackNotifier(bot_token=token)
        self.cst = pytz.timezone('US/Central')

    def respond_to_time_query(self, event):
        """Respond to time-related messages"""
        text = event['text'].lower()

        # Match time queries
        if any(phrase in text for phrase in [
            "what time is it",
            "current time",
            "what's the time",
            "time?"
        ]):
            current_time = datetime.now(self.cst)
            response = f"The current time is {current_time.strftime('%I:%M:%S %p %Z on %Y-%m-%d')}"

            self.notifier.notify(
                message=response,
                channel=event['channel']
            )

    @RTMClient.run_on(event="message")
    def handle_message(self, **payload):
        """Handle incoming messages"""
        event = payload['data']

        # Skip bot messages
        if 'subtype' in event and event['subtype'] == 'bot_message':
            return

        # Process time queries
        self.respond_to_time_query(event)

    def start(self):
        """Start the RTM connection"""
        self.client.start()

# Main entry point
if __name__ == "__main__":
    import os
    token = os.getenv('SLACK_BOT_TOKEN')
    bot = SlackTimeBot(token=token)
    bot.start()
```

**Configuration for RTM Agent:**
```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token"
export SLACK_AGENT_CHANNELS="C1234567890,C0987654321"  # Optional
export SLACK_AGENT_POLL_INTERVAL=5  # Optional
python -m slack_agent
```

## Code Style & Conventions

### Type Hints

**Always use type hints:**
```python
# Good
def notify_milestone(
    message: str,
    channel: str | None = None,
    level: str = "info"
) -> None:
    """Send a milestone notification."""
    pass

# Avoid
def notify_milestone(message, channel=None, level="info"):
    pass
```

### Docstrings

**Use Google-style docstrings:**
```python
def send_message(
    message: str,
    channel: str,
    level: str = "info"
) -> dict:
    """Send a message to Slack.

    Args:
        message: The message text to send.
        channel: Target Slack channel (e.g., "#general").
        level: Message level (info, success, warning, error).

    Returns:
        Response data from Slack API.

    Raises:
        SlackNotificationError: If the API request fails.
    """
    pass
```

### Error Messages

**Include context in error messages:**
```python
# Good
raise SlackNotificationError(
    f"Failed to send message to {channel}: {str(error)}"
)

# Avoid
raise SlackNotificationError("API Error")
```

### Logging

**Use appropriate log levels:**
```python
logger.debug("Sending message to channel: #general")  # Development info
logger.info("Message sent successfully")              # Success events
logger.warning("Rate limit approaching")              # Warnings
logger.error("Failed to send message")                # Errors
logger.critical("Bot disconnected")                   # Critical issues
```

## Naming Conventions

The project follows Python PEP 8:

- **Functions/Variables:** `snake_case`
  - Good: `notify_milestone`, `bot_token`, `max_retries`
  - Avoid: `notifyMilestone`, `BotToken`, `MAXRETRIES`

- **Classes:** `PascalCase`
  - Good: `SlackNotifier`, `SlackHandler`, `Config`
  - Avoid: `slack_notifier`, `SLACKNOTIFIER`

- **Constants:** `UPPER_SNAKE_CASE`
  - Good: `DEFAULT_TIMEOUT`, `MAX_RETRY_ATTEMPTS`
  - Avoid: `default_timeout`, `MaxRetryAttempts`

## Configuration Examples

### Development Configuration

```bash
# .env (development)
SLACK_BOT_TOKEN=xoxb-dev-token
SLACK_DEFAULT_CHANNEL=#dev-notifications
SLACK_TIMEOUT=30
SLACK_MAX_RETRIES=3
```

### Production Configuration

```bash
# Environment variables (production)
SLACK_BOT_TOKEN=xoxb-prod-token
SLACK_DEFAULT_CHANNEL=#alerts
SLACK_TIMEOUT=10
SLACK_MAX_RETRIES=5
```

### Multi-Channel Configuration

```python
# Send to different channels based on level
def notify_by_level(message: str, level: str):
    channel_map = {
        "error": "#error-logs",
        "warning": "#warnings",
        "info": "#general",
        "success": "#deployments"
    }
    notify_milestone(
        message=message,
        channel=channel_map.get(level, "#general"),
        level=level
    )
```

## See Also

- [Architecture](architecture.md) - System design
- [Definition of Done](definition-of-done.md) - Quality standards
- [Slack Agent Usage Guide](slack-agent-usage.md) - RTM agent documentation
- [MCP Service Setup](mcp-service-setup.md) - FastMCP server details

---
Last Updated: 2026-01-29
