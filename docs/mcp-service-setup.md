# Slack MCP Service Setup Guide

This document provides setup and usage instructions for the Slack MCP (Model Context Protocol) service, which allows AI agents to send notifications to Slack channels.

## Overview

The Slack MCP service extends the slack-notifications library by providing a standardized MCP interface that AI agents can use to send messages to Slack channels. This enables seamless integration between AI assistants and Slack communication workflows.

## Features

- **MCP Protocol Support**: Full FastMCP v2.0 compatibility
- **Multiple Message Types**: Send info, success, warning, and error messages
- **Flexible Configuration**: Environment variables or TOML configuration
- **Error Handling**: Comprehensive error reporting for troubleshooting
- **Async Support**: Built on async architecture for performance

## Prerequisites

- Python 3.8+
- Slack workspace with bot token
- FastMCP-compatible AI agent or MCP client

## Installation

The MCP service is included with the slack-agent project. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: Environment Variables

Set the following environment variables:

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_DEFAULT_CHANNEL="#general"
export SLACK_TIMEOUT="30"
export SLACK_MAX_RETRIES="3"
```

### Option 2: TOML Configuration File

Create `slack_notifications.toml`:

```toml
[slack]
bot_token = "xoxb-your-bot-token-here"
default_channel = "#general"
timeout = 30
max_retries = 3
```

### Option 3: Runtime Configuration

Use the MCP `configure_slack_notifications` tool to configure at runtime.

## Running the MCP Server

Start the MCP server:

```bash
python slack_mcp_server.py
```

The server will start and listen for MCP connections. You should see:

```
2025-12-25 11:00:00,000 - slack_notifications.mcp_server - INFO - Starting Slack MCP server...
```

## Available MCP Tools

### send_slack_message

Send a notification message to Slack.

**Parameters:**
- `message` (string, required): The message to send
- `channel` (string, optional): Target channel (uses default if not specified)
- `level` (string, optional): Message level - "info", "success", "warning", or "error"

**Example:**
```
send_slack_message("Deployment completed successfully", "#devops", "success")
```

### send_slack_success

Send a success notification (convenience wrapper).

**Parameters:**
- `message` (string, required): The success message
- `channel` (string, optional): Target channel

**Example:**
```
send_slack_success("Build passed", "#ci-cd")
```

### send_slack_warning

Send a warning notification (convenience wrapper).

**Parameters:**
- `message` (string, required): The warning message
- `channel` (string, optional): Target channel

**Example:**
```
send_slack_warning("High memory usage detected", "#alerts")
```

### send_slack_error

Send an error notification (convenience wrapper).

**Parameters:**
- `message` (string, required): The error message
- `channel` (string, optional): Target channel

**Example:**
```
send_slack_error("Database connection failed", "#errors")
```

### configure_slack_notifications

Configure Slack notifications globally.

**Parameters:**
- `bot_token` (string, optional): Slack bot token
- `default_channel` (string, optional): Default channel
- `timeout` (integer, optional): Request timeout in seconds
- `max_retries` (integer, optional): Maximum retry attempts

**Example:**
```
configure_slack_notifications("xoxb-new-token", "#notifications", 60, 5)
```

## Integration with AI Agents

### Claude Desktop Integration

To integrate with Claude Desktop, add the MCP server to your configuration:

```json
{
  "mcpServers": {
    "slack-notifications": {
      "command": "python",
      "args": ["/path/to/slack_mcp_server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_DEFAULT_CHANNEL": "#general"
      }
    }
  }
}
```

### Other MCP Clients

For other MCP-compatible clients, configure them to connect to the running MCP server process.

## Usage Examples

### Basic Notification

```
AI Agent: I need to notify the team about the successful deployment.

MCP Tool Call: send_slack_success("🚀 Production deployment completed successfully! All systems operational.", "#devops")
```

### Error Alert

```
AI Agent: The build failed, I should alert the team.

MCP Tool Call: send_slack_error("❌ Build failed on main branch. Check CI/CD pipeline for details.", "#builds")
```

### Configuration Update

```
AI Agent: I need to change the default channel for notifications.

MCP Tool Call: configure_slack_notifications(default_channel="#team-updates")
```

## Error Handling

The MCP service provides detailed error messages:

- **Configuration Errors**: "❌ Slack configuration error: [details]"
- **API Errors**: "❌ Failed to send Slack message: [details]"
- **Network Errors**: "❌ Unexpected error sending Slack message: [details]"

## Security Considerations

- Store bot tokens securely (environment variables, not in code)
- Use appropriate channel permissions for your bot
- Monitor token usage and rotate regularly
- Consider IP restrictions for bot access

## Troubleshooting

### Server Won't Start

1. Check Python version (3.8+ required)
2. Verify all dependencies are installed
3. Ensure SLACK_BOT_TOKEN is set
4. Check for port conflicts if specifying custom ports

### Messages Not Sending

1. Verify bot token is valid and has appropriate scopes
2. Check channel permissions for the bot
3. Confirm channel names start with # or @
4. Review Slack API rate limits

### MCP Connection Issues

1. Ensure the MCP server is running before connecting clients
2. Verify client configuration matches server setup
3. Check firewall settings if running on different machines
4. Review client-specific MCP configuration requirements

## Performance Notes

- Messages are sent synchronously for reliability
- Consider rate limiting for high-volume notifications
- The service uses connection pooling for efficiency
- Async operations are supported for high-throughput scenarios

## Support

For issues or questions:

1. Check the main project documentation
2. Review Slack API documentation for bot setup
3. Examine server logs for detailed error information
4. Test with minimal configuration to isolate issues