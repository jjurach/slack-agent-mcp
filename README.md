# Slack Notifications

A simple Python library for sending Slack notifications at application milestones.

## Features

- 🚀 Simple API for milestone notifications
- ⚙️ Flexible configuration via environment variables or config files
- 🔄 Async support for non-blocking notifications
- 🛡️ Comprehensive error handling and logging
- 📝 Full type hints and documentation
- 🧪 Well-tested with examples
- 🤖 **NEW:** MCP Server for AI agent integration
- ⏰ **NEW:** Real-time Slack Agent with time queries

## Installation

```bash
pip install slack-notifications
```

## Quick Start

1. **Set up your Slack app and get a bot token:**
   - Go to [Slack API](https://api.slack.com/apps)
   - Create a new app or use an existing one
   - Add the bot to your workspace
   - Copy the Bot User OAuth Token

2. **Configure environment variables:**
   ```bash
   # Copy the example file and fill in your values
   cp .env.example .env
   # Edit .env with your actual Slack bot token
   ```

   Or set environment variables directly:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
   export SLACK_DEFAULT_CHANNEL="#general"
   ```

3. **Use in your Python code:**
   ```python
   from slack_notifications import notify_milestone

   # Send a simple milestone notification
   notify_milestone("Application started successfully!")

   # Send to a specific channel with custom level
   notify_milestone("Database migration completed", channel="#dev-ops", level="info")

   # Send error notifications
   notify_milestone("Critical error occurred", level="error")
   ```

## Configuration

The application supports multiple configuration methods, automatically loading in this priority order:
1. Environment variables (highest priority)
2. `.env` file in the current directory
3. `slack_notifications.toml` file
4. Built-in defaults (lowest priority)

### Using .env Files (Recommended)

For secure, static deployment configuration:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   ```bash
   # Required
   SLACK_BOT_TOKEN=xoxb-your-actual-bot-token

   # Optional (with defaults shown)
   SLACK_DEFAULT_CHANNEL=#general
   SLACK_TIMEOUT=30
   SLACK_MAX_RETRIES=3
   ```

**Security Note:** The `.env` file is automatically ignored by Git and should never be committed to version control.

### Environment Variables

You can also set configuration via environment variables:

- `SLACK_BOT_TOKEN`: Your Slack bot token (required)
- `SLACK_DEFAULT_CHANNEL`: Default channel for notifications (default: "#general")
- `SLACK_TIMEOUT`: Request timeout in seconds (default: 30)
- `SLACK_MAX_RETRIES`: Maximum retry attempts (default: 3)

### TOML Configuration File

Alternatively, use a `slack_notifications.toml` file:

```toml
# slack_notifications.toml
[slack]
bot_token = "xoxb-your-bot-token-here"
default_channel = "#notifications"
timeout = 30
max_retries = 3
```

## Async Usage

For non-blocking notifications in async applications:

```python
import asyncio
from slack_notifications import notify_milestone_async

async def main():
    # Send notification asynchronously
    await notify_milestone_async("Async operation completed")

    # Continue with other work immediately
    await do_other_work()

asyncio.run(main())
```

## Error Handling

The library includes comprehensive error handling:

```python
from slack_notifications import notify_milestone, SlackNotificationError

try:
    notify_milestone("Test notification")
    print("Notification sent successfully!")
except SlackNotificationError as e:
    print(f"Failed to send notification: {e}")
```

## Advanced Usage

### Custom Configuration

```python
from slack_notifications import SlackNotifier

# Create notifier with custom config
notifier = SlackNotifier(
    bot_token="xoxb-custom-token",
    default_channel="#custom-channel",
    timeout=60
)

notifier.notify("Custom notification")
```

### Logging Integration

The library integrates with Python's logging module:

```python
import logging
from slack_notifications import SlackHandler

# Add Slack handler to your logger
logger = logging.getLogger()
slack_handler = SlackHandler(channel="#logs", level=logging.ERROR)
logger.addHandler(slack_handler)

# Now errors will be sent to Slack automatically
logger.error("This error will appear in Slack!")
```

## MCP Server for AI Agents

The slack-agent project now includes a FastMCP server that allows AI agents to send notifications to Slack channels via the Model Context Protocol (MCP).

### Starting the MCP Server

```bash
python slack_mcp_server.py
```

### Available MCP Tools

- `send_slack_message(message, channel, level)` - Send a notification message
- `send_slack_success(message, channel)` - Send a success notification
- `send_slack_warning(message, channel)` - Send a warning notification
- `send_slack_error(message, channel)` - Send an error notification
- `configure_slack_notifications(...)` - Configure Slack settings

### AI Agent Integration

AI agents can use these tools to send Slack messages. For example:

```
AI Agent: I need to notify the team about the deployment.

MCP Tool Call: send_slack_success("🚀 Production deployment completed successfully!", "#devops")
```

See [doc/mcp-service-setup.md](doc/mcp-service-setup.md) for detailed setup and usage instructions.

## Model Configuration (Conceptual Change)

The slack-agent project supports a conceptual change in how AI models are configured and managed. This change introduces a clear separation between **models** (what users interact with) and **backends** (provider implementations).

### Model vs Backend Concept

- **Model**: User-facing interface with friendly names, descriptions, and capabilities
- **Backend**: Actual provider implementation (OpenAI, Anthropic, Ollama, etc.)

This enables flexible routing, failover, cost optimization, and multi-provider support.

### Configuration Structure

```yaml
# models: What users see and select
models:
  creative-writer:
    backend: "anthropic/claude-3-sonnet"
    description: "Creative writing assistant"
    capabilities: ["chat", "completion"]

  fast-chat:
    backend: "ollama/llama3.2:3b"
    description: "Fast local responses"

# backends: Provider configurations
backends:
  anthropic:
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"

  ollama:
    provider: "ollama"
    base_url: "http://localhost:11434"
```

### Benefits

- **Provider Agnosticism**: Switch providers without changing user-facing model names
- **Failover**: Automatic fallback to alternative providers
- **Cost Optimization**: Route to cheapest available provider
- **Load Balancing**: Distribute requests across multiple backends

See [doc/model-backend-concept.md](doc/model-backend-concept.md) for complete conceptual documentation and [examples/model_config_example.yaml](examples/model_config_example.yaml) for configuration examples.

## Slack Agent

The project includes a Slack bot that monitors channels using the Web API and responds to time queries with current CST time.

### Running the Slack Agent

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
python slack_agent.py
```

### Configuration

The Slack Agent supports additional configuration:

```bash
# Optional: Comma-separated list of channel IDs to monitor
export SLACK_AGENT_CHANNELS="C1234567890,C0987654321"

# Optional: Polling interval in seconds (default: 5)
export SLACK_AGENT_POLL_INTERVAL=5
```

If `SLACK_AGENT_CHANNELS` is not set, the agent will automatically discover and monitor channels with "general" in their name.

### Time Query Responses

The agent responds to exact time-related queries:

- "what time is it" → "The current time is 11:00:00 AM CST on 2025-12-25"
- "what's the time?" → Same response
- "time" → Same response
- "current time" → Same response

### Logging

All interactions are logged to stdout with CST timestamps:

```
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] Starting Slack Agent...
2025-12-25 11:00:00 CST - slack_agent - INFO - Bot authenticated as user: U1234567890
2025-12-25 11:00:00 CST - slack_agent - INFO - Monitoring channels: C1234567890
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] MESSAGE - Channel: C1234567890, User: U1234567890, Text: 'what time is it?'
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] RESPONSE - Sent time to channel C1234567890: The current time is 11:00:00 AM CST on 2025-12-25
```

See [doc/slack-agent-usage.md](doc/slack-agent-usage.md) for complete setup and usage instructions.

## Development

### Setup

```bash
git clone https://github.com/yourusername/slack-notifications.git
cd slack-notifications
pip install -e ".[dev,test]"
```

### Testing

```bash
pytest
```

### Building

```bash
python -m build
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.