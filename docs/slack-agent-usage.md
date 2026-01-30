# Slack Agent Usage Guide

This document provides setup and usage instructions for the Slack Agent script, which connects to Slack via Real Time Messaging (RTM) and responds to time queries.

## Overview

The Slack Agent is a real-time Slack bot that monitors messages and responds to time-related queries. It specifically handles "what time is it?" questions by providing the current time in Central Standard Time (CST). All interactions are logged to stdout with timestamps for monitoring and debugging.

## Features

- **Real-Time Messaging**: Connects to Slack via RTM for instant message processing
- **Time Queries**: Responds to various time-related questions
- **Timestamped Logging**: All interactions logged to stdout with CST timestamps
- **Central Time Focus**: Provides accurate CST time with proper timezone handling
- **Foreground Operation**: Runs continuously in foreground for real-time monitoring
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

- Python 3.8+
- Slack workspace with bot token
- Bot token with appropriate permissions (see Slack App setup below)

## Slack App Setup

### 1. Create a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enter app name (e.g., "Time Bot") and select workspace
4. Click "Create App"

### 2. Configure Bot Token Scopes

In your app settings:

1. Go to "OAuth & Permissions" in the sidebar
2. Under "Scopes", add these bot token scopes:
   - `channels:read` - View basic information about public channels
   - `groups:read` - View basic information about private channels
   - `im:read` - View basic information about direct messages
   - `mpim:read` - View basic information about group direct messages
   - `channels:history` - View messages and other content in public channels
   - `groups:history` - View messages and other content in private channels
   - `im:history` - View messages and other content in direct messages
   - `mpim:history` - View messages and other content in group direct messages
   - `chat:write` - Send messages as the bot

### 3. Install App to Workspace

1. Go to "Install App" in the sidebar
2. Click "Install to Workspace"
3. Authorize the required permissions
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Add Bot to Channels (Optional)

To respond in specific channels, invite the bot:

```
/invite @YourBotName
```

## Installation

The Slack Agent is included with the slack-agent project. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Set the required environment variable:

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
```

## Running the Slack Agent

Start the agent:

```bash
python slack_agent.py
```

The agent will connect to Slack and begin monitoring messages. You should see output like:

```
2025-12-25 11:00:00,000 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] Starting Slack Agent...
2025-12-25 11:00:01,000 CST - slack_agent - INFO - [2025-12-25 11:00:01 CST] RTM connection established - Hello from Slack!
```

## Time Query Responses

The agent responds to messages containing time-related queries (case-insensitive):

### Supported Queries

- "what time is it"
- "what time is it?"
- "what's the time"
- "what's the time?"
- "what is the time"
- "what is the time?"
- "time"
- "current time"

### Response Format

When triggered, the agent responds with:

```
The current time is 11:00:00 AM CST on 2025-12-25
```

### Example Interaction

```
User: Hey bot, what time is it?
Bot: The current time is 11:00:00 AM CST on 2025-12-25

[Log Output]
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] MESSAGE - Channel: C1234567890, User: U1234567890, Text: 'Hey bot, what time is it?'
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] RESPONSE - Sent time to channel C1234567890: The current time is 11:00:00 AM CST on 2025-12-25
```

## Logging and Monitoring

### Log Format

All interactions are logged to stdout with the format:

```
[timestamp] LEVEL - [CST_timestamp] EVENT_TYPE - details
```

### Log Types

- **Connection Events**: RTM connection established/disconnected
- **Messages**: All incoming messages with channel, user, and text
- **Responses**: Bot responses with channel and content
- **Errors**: Any errors encountered during operation

### Sample Log Output

```
2025-12-25 11:00:00 CST - slack_agent - INFO - [2025-12-25 11:00:00 CST] Starting Slack Agent...
2025-12-25 11:00:01 CST - slack_agent - INFO - [2025-12-25 11:00:01 CST] RTM connection established - Hello from Slack!
2025-12-25 11:00:15 CST - slack_agent - INFO - [2025-12-25 11:00:15 CST] MESSAGE - Channel: C1234567890, User: U1234567890, Text: 'what time is it?'
2025-12-25 11:00:15 CST - slack_agent - INFO - [2025-12-25 11:00:15 CST] RESPONSE - Sent time to channel C1234567890: The current time is 11:00:15 AM CST on 2025-12-25
2025-12-25 11:05:30 CST - slack_agent - INFO - [2025-12-25 11:05:30 CST] MESSAGE - Channel: C1234567890, User: U9876543210, Text: 'hello bot'
2025-12-25 11:30:00 CST - slack_agent - INFO - [2025-12-25 11:30:00 CST] RTM connection closed - Goodbye from Slack!
```

## Usage Scenarios

### Development Monitoring

Run the agent during development to monitor Slack activity:

```bash
python slack_agent.py | tee slack_agent_$(date +%Y%m%d_%H%M%S).log
```

### Production Deployment

For production use, consider:

- Running as a system service
- Log rotation for long-term monitoring
- Monitoring the log output for errors
- Setting up alerts for disconnection events

### Testing

Test the agent by sending time queries in channels where the bot is present:

- Direct messages: `@YourBot what time is it?`
- Channel messages: `what time is it?`
- Various phrasings to test query recognition

## Stopping the Agent

The agent runs continuously until interrupted. To stop:

- Press `Ctrl+C` in the terminal
- Send SIGTERM signal to the process
- The agent will log the shutdown and close the RTM connection gracefully

## Troubleshooting

### Connection Issues

**Problem**: Agent fails to connect to Slack

**Solutions**:
1. Verify `SLACK_BOT_TOKEN` is set correctly
2. Check token permissions in Slack App settings
3. Ensure bot is invited to channels (if needed)
4. Check network connectivity to Slack APIs

**Log Output**:
```
2025-12-25 11:00:00 CST - slack_agent - ERROR - [2025-12-25 11:00:00 CST] Error in Slack Agent: [connection error details]
```

### No Responses to Queries

**Problem**: Bot sees messages but doesn't respond to time queries

**Solutions**:
1. Verify bot has `chat:write` permission
2. Check that query text matches recognition patterns
3. Ensure bot is in the channel where messages are sent
4. Review logs for error messages during response attempts

### Timezone Issues

**Problem**: Time responses show incorrect timezone

**Solutions**:
1. Verify system has correct timezone settings
2. Check that `pytz` library is installed
3. Confirm CST timezone is available (`America/Chicago`)
4. Test timezone conversion manually

### Logging Problems

**Problem**: No log output or logs going to wrong location

**Solutions**:
1. Ensure stdout is not redirected if logs should appear in terminal
2. Check file permissions if redirecting to files
3. Verify Python logging configuration
4. Test with minimal logging setup

## Performance Considerations

- **RTM Connection**: Maintains persistent WebSocket connection
- **Message Processing**: Processes each message individually
- **Rate Limiting**: Subject to Slack API rate limits
- **Memory Usage**: Minimal memory footprint for single-channel monitoring
- **CPU Usage**: Low CPU usage during normal operation

## Security Notes

- Store bot tokens securely (environment variables, not in code)
- Monitor token usage for unauthorized access
- Regularly rotate bot tokens
- Limit bot permissions to minimum required scopes
- Consider network-level security for RTM connections

## Integration with Other Tools

### Log Analysis

Parse logs with tools like `grep`, `awk`, or log analysis platforms:

```bash
# Count time queries
grep "RESPONSE.*time" slack_agent.log | wc -l

# Find error patterns
grep "ERROR" slack_agent.log

# Extract message timeline
grep "MESSAGE\|RESPONSE" slack_agent.log | sort
```

### Monitoring Systems

Integrate with monitoring tools:

- Send logs to ELK stack for analysis
- Set up alerts for disconnection events
- Monitor response times for performance tracking
- Track query frequency for usage analytics

## Support

For issues or questions:

1. Review the log output for error details
2. Test with minimal configuration to isolate problems
3. Check Slack API status and documentation
4. Verify bot permissions and channel access
5. Test RTM connection manually using Slack API tools

## Advanced Configuration

### Custom Time Queries

To extend the agent with additional query patterns, modify the `_is_time_query` method in `slack_agent.py`.

### Multiple Timezones

The agent currently focuses on CST. To support multiple timezones, modify the response logic to accept timezone parameters.

### Custom Responses

To change response formatting, modify the `_respond_with_time` method with custom time string formatting.