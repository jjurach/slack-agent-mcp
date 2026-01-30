# Agent Instructions for slack-agent MCP Server

This document describes the slack-agent tools and how agents should use them effectively.

## Tool Catalog

### send_slack_message

Sends a message to a Slack channel or direct message.

**Parameters:**
- `message` (string, required): The message to send (max 40,000 characters)
- `channel` (string, optional): Target channel or DM. Format: `#channel` or `@user`. If not specified, uses default channel from configuration.
- `level` (string, optional): Message severity level. Options: `"info"` (default), `"success"`, `"warning"`, `"error"`. Affects message formatting/emoji.

**Returns:**
```json
{
  "status": "success",
  "data": {
    "message": "Message sent successfully to #channel",
    "channel": "#channel",
    "timestamp": "1234567890.123456"
  },
  "request_id": "uuid-here"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description",
  "request_id": "uuid-here"
}
```

**Examples:**
- Send to default channel: `send_slack_message("Build complete!")`
- Send to specific channel: `send_slack_message("Meeting at 3pm", channel="#announcements")`
- Send with level: `send_slack_message("Deployment failed!", level="error")`

**Common Errors:**
- `not_in_channel` - Bot is not a member of the channel. Solution: Add bot to channel.
- `channel_not_found` - Channel doesn't exist. Solution: Use `send_slack_message` with correct channel name.
- `invalid_auth` - Token is invalid or expired. Solution: Check bot token in configuration.

---

### send_slack_success

Convenience function to send a success message.

**Parameters:**
- `message` (string, required): The success message
- `channel` (string, optional): Target channel (format: `#channel` or `@user`)

**Returns:** Same as send_slack_message

**Example:**
```
send_slack_success("✓ Deployment successful", channel="#deployments")
```

Equivalent to: `send_slack_message("✓ Deployment successful", channel="#deployments", level="success")`

---

### send_slack_warning

Convenience function to send a warning message.

**Parameters:**
- `message` (string, required): The warning message
- `channel` (string, optional): Target channel (format: `#channel` or `@user`)

**Returns:** Same as send_slack_message

**Example:**
```
send_slack_warning("⚠️ High memory usage detected", channel="#alerts")
```

---

### send_slack_error

Convenience function to send an error message.

**Parameters:**
- `message` (string, required): The error message
- `channel` (string, optional): Target channel (format: `#channel` or `@user`)

**Returns:** Same as send_slack_message

**Example:**
```
send_slack_error("✗ Build failed: test suite error", channel="#ci-alerts")
```

---

### configure_slack_notifications

Configures Slack notifications settings. Note: This typically happens at application startup and doesn't need to be called by agents.

**Parameters:**
- `bot_token` (string, optional): Slack bot token (xoxb-*)
- `default_channel` (string, optional): Default notification channel
- `timeout` (integer, optional): Request timeout in seconds (1-300, default: 30)
- `max_retries` (integer, optional): Maximum retry attempts (0-10, default: 3)

**Returns:**
```json
{
  "status": "success",
  "message": "Slack notifications configured successfully",
  "request_id": "uuid-here"
}
```

**Note:** This tool is rarely needed in agent workflows as configuration is usually done via environment variables or config files.

---

## Domain Context: Slack Data Model

Agents should understand these Slack concepts:

### Channels
- **Format:** `#channel-name` (channels are case-insensitive)
- **Types:** Public channels (anyone can join) and private channels (invite-only)
- **Special Channels:** `#general` (default), `#random`
- **Private Channels:** Prefix with `#` just like public channels
- **Finding Channels:** Use channel names, not IDs (bot will resolve)

### Direct Messages
- **Format:** `@username`
- **Use Cases:** Private notifications, personal messages
- **Note:** Need to know the username

### Messages
- **Limit:** 40,000 characters per message
- **Format:** Plain text (Slack will auto-linkify URLs)
- **Markdown:** Limited support (emphasis, code blocks, lists)
- **Timestamps:** Message timestamps (ts) are used internally for threading

### Message Levels
- **info** - General information (default, no emoji)
- **success** - Operation succeeded (✓ or 🎉)
- **warning** - Something needs attention (⚠️ or 🤔)
- **error** - Something failed (✗ or ❌)

### Bot Capabilities
- Send messages to channels the bot is a member of
- Send direct messages to users
- Read message timestamps for logging
- Cannot react to messages (would require additional permissions)
- Cannot delete messages (would require additional permissions)

### Limitations
- Cannot send to channels the bot isn't a member of (get `not_in_channel` error)
- Cannot access message history (read-only send capability)
- Cannot create channels
- Cannot manage users or permissions

## Agent Usage Patterns

### Pattern 1: Simple Notification

```
send_slack_message("Deploy complete! Version 1.2.3 is live.")
```

### Pattern 2: Status Updates with Channels

```
if build_successful:
    send_slack_success("Build completed", channel="#builds")
else:
    send_slack_error("Build failed", channel="#alerts")
```

### Pattern 3: Multi-Part Updates

```
# Alert channel first
send_slack_error("Database migration failed", channel="#alerts")

# Then notify engineering
send_slack_message("Need immediate attention", channel="@engineering-lead")

# Log to general
send_slack_message("Issue: DB migration script had syntax error", channel="#team-updates")
```

### Pattern 4: Progress Updates

```
send_slack_message("Starting deployment...", channel="#deployments")
# Do work...
send_slack_message("Build started", channel="#deployments")
# Do more work...
send_slack_success("Build complete", channel="#deployments")
```

### Pattern 5: Error Handling

```
try:
    # Do something risky
except Exception as e:
    send_slack_error(f"Failed: {str(e)}", channel="#alerts")
    # Handle error...
```

## Best Practices for Agents

### ✅ DO:
- Use appropriate message levels (info/success/warning/error)
- Use channel mentions intelligently (#alerts for critical, #general for routine)
- Keep messages concise and actionable
- Include relevant context (what happened, why it matters)
- Use direct messages for sensitive or private updates
- Break long messages into multiple sends if needed
- Include timestamps or version numbers for clarity

### ❌ DON'T:
- Send the same message repeatedly (batch or wait before sending)
- Ignore channel membership errors - handle and retry or notify
- Mix multiple unrelated issues in one message
- Use error level for non-critical issues
- Send to channels the bot doesn't have access to
- Include sensitive credentials in messages (they're masked in logs)
- Send message > 40,000 characters (Slack limit)

## Error Handling Guide

### Error: `not_in_channel`
**What it means:** Bot tried to send to a channel it's not a member of.
**Recovery:**
1. Try default channel instead: `send_slack_message(msg)`
2. Notify user to add bot to channel
3. List available channels for user

### Error: `channel_not_found`
**What it means:** Channel name is invalid or doesn't exist.
**Recovery:**
1. Check channel name format (starts with # or @)
2. Suggest available channels
3. Use default channel as fallback

### Error: `invalid_auth`
**What it means:** Bot token is invalid, expired, or revoked.
**Recovery:**
1. Log the error with request_id for debugging
2. User must refresh bot token
3. Check token starts with `xoxb-`

### Error: `message_text_too_long`
**What it means:** Message exceeds 40,000 character limit.
**Recovery:**
1. Split message into multiple sends
2. Use threads for related messages
3. Summarize lengthy content

### Error: `timeout`
**What it means:** Slack API didn't respond in time.
**Recovery:**
1. Retry with exponential backoff (included in tool)
2. Check network connectivity
3. Check Slack status page
4. Log with request_id for analysis

## Request ID Tracking

Every response includes a `request_id`:
```json
{"status": "success", "data": {...}, "request_id": "abc-123-def-456"}
```

**Use request_id for:**
- Debugging specific calls in audit logs
- Correlating multiple related calls
- Reporting issues to humans
- Trace routing through distributed systems

Example: `"Check logs for request_id: abc-123-def-456"`

## Configuration

The bot's behavior is controlled by environment variables and config files:

### Environment Variables
- `SLACK_BOT_TOKEN` - Required: Bot token
- `SLACK_DEFAULT_CHANNEL` - Default channel (#general)
- `SLACK_TIMEOUT` - Request timeout (30 seconds default)
- `SLACK_MAX_RETRIES` - Retry attempts (3 default)
- `SLACK_AGENT_PROFILE` - Profile to use (default)

### Profile Configuration
Agents don't need to configure this, but should be aware:
- Multiple profiles can be set up for different workspaces
- Profile is selected via environment or config file
- Each profile has its own token and settings

## Security and Privacy

### Credential Protection
- Bot tokens are **never** logged (masked as `xoxb-****-****`)
- Slack webhook URLs are masked in logs
- User tokens and app tokens are also masked
- Debug mode (`SLACK_AGENT_DEBUG=1`) disables masking (development only)

### Access Control
- Bot can only send to channels it's a member of
- Bot cannot read message history (send-only)
- Bot cannot impersonate users
- Permissions are configured at the Slack workspace level

### Audit Trail
- All tool calls are logged with request_id, timestamp, success/failure
- Audit log location: `~/.config/slack-agent/audit.log`
- Useful for debugging and compliance

## Integration Example

```python
# Check if operation succeeded
if migration_successful:
    # Send success to team channel
    send_slack_success(
        "Database migration to v2 complete!",
        channel="#database-team"
    )
    
    # Notify monitoring team
    send_slack_message(
        "Connection pooling updated. Monitor for anomalies.",
        channel="#monitoring"
    )
else:
    # Alert on failure
    send_slack_error(
        f"Migration failed: {error_message}",
        channel="#alerts"
    )
    
    # Notify on-call engineer
    send_slack_message(
        "Need help with migration rollback @engineering-oncall",
        channel="@engineering-oncall"
    )
```

## Troubleshooting

For agents experiencing issues:

1. **Check request_id in response** - Include this when asking for help
2. **Review audit log** - `slack-agent-cli debug audit-log --tail 20`
3. **Verify configuration** - `slack-agent-cli config validate`
4. **Test connectivity** - `slack-agent-cli test auth`
5. **Enable verbose logging** - `SLACK_AGENT_VERBOSE=1`

## When to Use Slack vs Other Tools

**Use slack-agent for:**
- Notifications about task completion/failures
- Team updates and announcements
- Alerts that need human attention
- Status reports
- Incident notifications

**Don't use for:**
- Data storage (use databases)
- Real-time communication (too slow)
- Secrets/credentials (masked anyway)
- High-frequency updates (rate limits apply)

## Rate Limiting

Slack API has rate limits:
- Typically 60 messages per minute per app
- Tool automatically retries transient failures
- Backoff strategy: 2s, 4s, 8s

If you hit limits:
- Batch related messages
- Add delays between sends
- Contact Slack support for rate limit exceptions

## Future Enhancements

Potential features for slack-agent (not yet implemented):
- Message reactions
- Threading support
- Slack Blocks (rich formatting)
- File uploads
- Emoji reactions to messages
- User mentions with @
