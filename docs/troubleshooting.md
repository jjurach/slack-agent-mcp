# Troubleshooting Guide

This guide helps diagnose and fix common issues with slack-agent.

## Configuration Issues

### "No valid Slack configuration found"

**Error Message:**
```
ValueError: No valid Slack configuration found. 
Please set SLACK_BOT_TOKEN environment variable or create ~/.config/slack-agent/config.json.
```

**Causes & Solutions:**

1. **Environment variable not set:**
   ```bash
   # Check if SLACK_BOT_TOKEN is set
   echo $SLACK_BOT_TOKEN
   
   # If empty, set it:
   export SLACK_BOT_TOKEN="xoxb-your-token"
   ```

2. **.env file not loaded:**
   - Ensure `.env` file exists in the project root
   - Copy from `.env.example` if needed: `cp .env.example .env`
   - Edit `.env` with your actual token

3. **Profile configuration file not found:**
   ```bash
   # Create default config
   slack-agent-cli config init
   
   # Or manually create:
   mkdir -p ~/.config/slack-agent
   # Create config.json as shown in development-guide.md
   ```

### "Bot token must start with 'xoxb-'"

**Cause:** Invalid token format in environment variable

**Solution:**
- Verify token format: Slack bot tokens start with `xoxb-`
- Check you're not using a user token (`xoxp-`) or app token (`xapp-`)
- Get correct token from: https://api.slack.com/apps
- Copy the full token (including `xoxb-` prefix)

### "Bot token appears to be too short"

**Cause:** Incomplete or truncated token

**Solution:**
- Verify you copied the entire token
- Token should be ~30-50 characters after `xoxb-`
- Check for extra spaces: `echo "$SLACK_BOT_TOKEN" | wc -c`

### "Profile 'X' not found"

**Error:**
```
ValueError: Profile 'work' not found in configuration
```

**Solution:**
1. List available profiles:
   ```bash
   slack-agent-cli config list-profiles
   ```

2. Use correct profile name:
   ```bash
   SLACK_AGENT_PROFILE=work slack-agent-cli test auth
   ```

3. Add missing profile to `~/.config/slack-agent/config.json`:
   ```json
   {
     "profiles": {
       "work": {
         "bot_token_env": "SLACK_WORK_BOT_TOKEN",
         "default_channel": "#work",
         "timeout": 30,
         "max_retries": 3
       }
     }
   }
   ```

## Authentication Issues

### "Invalid token" or "invalid_auth"

**Error Message:**
```
Error: invalid_auth
The token you provided was invalid
```

**Causes & Solutions:**

1. **Token is expired or revoked:**
   - Get a new token from https://api.slack.com/apps
   - Go to "OAuth & Permissions" → "Bot Token Scopes"
   - Copy the new token and update environment variable

2. **Token has insufficient permissions:**
   - Go to app settings: https://api.slack.com/apps
   - Ensure "chat:write" scope is enabled
   - For message reactions: add "reactions:write"
   - Reinstall the app in your workspace

3. **Token is for wrong workspace:**
   - Verify you're using token for correct Slack workspace
   - Each workspace requires its own token

4. **Credentials are masked in logs:**
   To see the actual error (development only):
   ```bash
   SLACK_AGENT_DEBUG=1 slack-agent-cli test auth
   ```

### Test authentication directly:

```bash
slack-agent-cli test auth
```

Expected output:
```
✓ Authentication successful
  Bot name:  my-bot
  Team:      My Team
  Bot ID:    U1234567890
```

## Permission Issues

### "not_in_channel" error

**Error:**
```
Error: not_in_channel
The bot is not in the specified channel
```

**Solution:**
1. Add bot to the channel:
   - Open Slack channel
   - Click channel name
   - Go to "Integrations" tab
   - Add the bot application

2. Or use default channel:
   ```bash
   # Don't specify channel; uses default from config
   slack-agent-cli test send-message "Hello"
   ```

3. Verify bot is in channel:
   ```bash
   slack-agent-cli test channels
   ```

### "missing_scope" error

**Error:**
```
Error: missing_scope
The token is missing the required scopes
```

**Solution:**
1. Go to app settings: https://api.slack.com/apps
2. Select your app
3. Go to "OAuth & Permissions"
4. Add required scopes under "Bot Token Scopes":
   - `chat:write` - Send messages
   - `reactions:write` - Add reactions
   - `pins:write` - Pin messages
   - `channels:read` - List channels
5. Click "Reinstall to Workspace"
6. Copy new bot token to environment

### "restricted_action" error

**Error:**
```
Error: restricted_action
Some API methods cannot be called by a bot
```

**Solution:**
- This action is not supported for bot tokens
- Some features require user tokens (xoxp-) instead
- Consider using different bot scopes or permissions

## Channel Issues

### "Channel not found"

**Error:**
```
Error: channel_not_found
The channel does not exist
```

**Solution:**
1. Check channel name format:
   - Channels: start with `#` (e.g., `#general`)
   - Direct messages: start with `@` (e.g., `@username`)

2. List available channels:
   ```bash
   slack-agent-cli test channels
   ```

3. Use correct channel name from list:
   ```bash
   slack-agent-cli test send-message "Hello" --channel "#general"
   ```

### "Channel is private"

**Error:**
```
Error: cant_post_to_private
Cannot post to a private channel without permission
```

**Solution:**
1. Add bot to the private channel:
   - Open Slack private channel
   - Click channel name
   - Go to "Members" tab
   - Add the bot application

2. Verify bot is member:
   ```bash
   slack-agent-cli test channels
   # Look for 🔒 (locked) channels with ✓ (member)
   ```

### "Channel name is reserved"

**Solution:**
- Some channel names are reserved (e.g., `#general`, `#random`)
- Use the channel ID instead of name if available
- Create a new channel with custom name

## Message Issues

### "Message too long"

**Error:**
```
Error: message_text_too_long
The message text is too long
```

**Solution:**
- Slack message limit is 40,000 characters
- Break message into smaller chunks
- Use threads for multi-part messages

### "Duplicate message"

**Issue:** Same message sent twice

**Causes & Solutions:**

1. **Retry logic triggered:**
   - Check audit log: `slack-agent-cli debug audit-log`
   - Network timeout may have caused retry
   - Message was actually sent (check Slack)

2. **Tool called twice:**
   - Check if agent is retrying the call
   - Verify circuit-breaker isn't triggering

### Message sent to wrong channel

**Solution:**
1. Verify channel parameter:
   ```bash
   slack-agent-cli test send-message "Test" --channel "#target-channel"
   ```

2. Check default channel in config:
   ```bash
   slack-agent-cli config show
   ```

3. If unsure, list available channels:
   ```bash
   slack-agent-cli test channels
   ```

## Network and Timeout Issues

### "Connection timeout"

**Error:**
```
Error: Connection timeout
```

**Causes & Solutions:**

1. **Network connectivity:**
   ```bash
   # Check internet connection
   ping api.slack.com
   
   # Check if Slack API is reachable
   curl https://slack.com
   ```

2. **Timeout value too low:**
   - Default timeout is 30 seconds
   - For slow networks, increase timeout:
     ```bash
     export SLACK_TIMEOUT=60
     ```

3. **Slack API outage:**
   - Check https://status.slack.com
   - Wait a few minutes and retry

### "Connection refused"

**Error:**
```
Error: Connection refused
```

**Solution:**
- Check internet connection: `ping 8.8.8.8`
- Check firewall isn't blocking slack.com
- Try from different network
- Check `SLACK_AGENT_VERBOSE=1` for more details

## Logging and Debugging

### Enable verbose logging:

```bash
export SLACK_AGENT_VERBOSE=1
slack-agent-cli test auth
```

### View audit log:

```bash
# Last 20 entries
slack-agent-cli debug audit-log --tail 20

# Filter by tool
slack-agent-cli debug audit-log --filter send_slack_message

# Real-time tail
tail -f ~/.config/slack-agent/audit.log
```

### Show resolved configuration:

```bash
slack-agent-cli debug show-config
```

**Note:** Shows actual bot token (use with caution)

### JSON logging format:

For log aggregation systems:

```bash
export SLACK_AGENT_JSON_LOGS=1
slack-agent-cli test send-message "Hello"
```

## Debugging Checklist

When troubleshooting, follow this checklist:

- [ ] Verify bot token is set and has correct format
- [ ] Test authentication: `slack-agent-cli test auth`
- [ ] Check bot has required scopes
- [ ] Verify channel exists and bot is member: `slack-agent-cli test channels`
- [ ] Enable verbose logging: `export SLACK_AGENT_VERBOSE=1`
- [ ] Check audit log for errors: `slack-agent-cli debug audit-log`
- [ ] Verify network connectivity: `ping api.slack.com`
- [ ] Check Slack API status: https://status.slack.com
- [ ] Review error message carefully for hints

## Getting Help

If you can't resolve the issue:

1. **Check logs:**
   ```bash
   SLACK_AGENT_VERBOSE=1 SLACK_AGENT_DEBUG=1 slack-agent-cli test auth
   ```

2. **Review audit log:**
   ```bash
   slack-agent-cli debug audit-log --tail 50
   ```

3. **Check configuration:**
   ```bash
   slack-agent-cli config validate
   ```

4. **Report issue with:**
   - Error message (sanitized)
   - Operating system
   - Python version: `python --version`
   - Steps to reproduce
   - Verbose log output

GitHub: https://github.com/yourusername/slack-agent/issues
