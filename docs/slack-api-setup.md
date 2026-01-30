# Slack API Setup Guide

This guide explains how to obtain and configure Slack API credentials for use with the Python Slack Notification Library.

## Prerequisites

- A Slack workspace where you have admin privileges
- A Slack account with permission to create apps

## Step 1: Create a Slack App

1. Go to the [Slack API website](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter your app name (e.g., "My Python Notifications")
5. Select the Slack workspace where you want to install the app
6. Click **"Create App"**

## Step 2: Configure Bot Token Scopes

Your app needs specific permissions to send messages to channels. Configure these in the OAuth & Permissions section:

1. In your app's settings, navigate to **"OAuth & Permissions"** in the left sidebar
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, add the following scopes:
   - `chat:write` - Send messages as the app
   - `chat:write.public` - Send messages to public channels (optional, for public channels)

## Step 3: Install the App to Your Workspace

1. In the **"OAuth & Permissions"** section, click **"Install to Workspace"**
2. Review the permissions and click **"Allow"**
3. After installation, you'll see your **"Bot User OAuth Token"** - this is your API key

## Step 4: Get Your Bot User OAuth Token

The **Bot User OAuth Token** is what you'll use as your `SLACK_BOT_TOKEN` environment variable. It looks like:
```
xoxb-your-bot-token-here
```

**Important:** Keep this token secure and never commit it to version control!

## Step 5: Add the Bot to Channels (Optional)

If you want the bot to post to specific channels:

1. Go to the channel in Slack
2. Type `/invite @YourBotName`
3. The bot will now be able to post to that channel

Alternatively, you can invite the bot programmatically in your code.

## Step 6: Configure Environment Variables

Create a `.env` file in your project root or set environment variables:

```bash
# Your bot token from Step 4
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# Default channel for notifications (optional)
SLACK_DEFAULT_CHANNEL=#general

# Your Slack workspace URL (optional, for reference)
SLACK_WORKSPACE=my-workspace.slack.com
```

## Step 7: Test Your Setup

Use the library's example scripts to test your configuration:

```bash
python examples/basic_usage.py
```

You should see a test message posted to your configured Slack channel.

## Troubleshooting

### "missing_scope" Error
- Make sure you've added the `chat:write` scope to your bot token
- Reinstall the app to your workspace after adding scopes

### "channel_not_found" Error
- Ensure the bot is invited to the target channel
- Check that the channel name is correct (include the # prefix)

### "invalid_auth" Error
- Verify your bot token is correct
- Make sure the token starts with `xoxb-`
- Check that the app is properly installed to your workspace

## Security Best Practices

- Never commit API tokens to version control
- Use environment variables or a secure configuration management system
- Regularly rotate your API tokens
- Limit bot permissions to only what's necessary

## Additional Resources

- [Slack API Documentation](https://api.slack.com/docs)
- [Bot Token Scopes Reference](https://api.slack.com/scopes)
- [Slack Developer Community](https://slack.dev/community)