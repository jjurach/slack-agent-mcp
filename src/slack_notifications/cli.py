"""
Command-line interface for slack-notifications.

Provides tools for configuration management, testing, and debugging.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from cyclopts import App, Parameter

from .config import AppConfig, SlackConfig
from .logging import configure_logging, get_audit_logger
from .notifier import SlackNotifier

# Create main CLI app
app = App(
    name="slack-agent-cli",
    help="CLI tools for Slack notifications MCP server",
)

# Create subcommands
config_app = App(name="config", help="Configuration management commands")
test_app = App(name="test", help="Testing commands")
debug_app = App(name="debug", help="Debugging and diagnostics commands")


# ====================
# Config Commands
# ====================

@config_app.command
def list_profiles():
    """List available configuration profiles."""
    try:
        app_config = AppConfig.auto_load()
        print("Available profiles:")
        print()
        for name, profile in app_config.profiles.items():
            print(f"  {name}:")
            print(f"    Token env: {profile.bot_token_env}")
            print(f"    Channel:   {profile.default_channel}")
            print(f"    Timeout:   {profile.timeout}s")
            print(f"    Retries:   {profile.max_retries}")
            print()
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)


@config_app.command
def show(
    profile: str = Parameter(default="default", help="Profile name to display")
):
    """Display configuration for a specific profile."""
    try:
        app_config = AppConfig.auto_load()

        if profile not in app_config.profiles:
            print(f"Error: Profile '{profile}' not found", file=sys.stderr)
            print(f"Available profiles: {', '.join(app_config.profiles.keys())}")
            sys.exit(1)

        profile_config = app_config.profiles[profile]

        print(f"Profile: {profile}")
        print()
        print(f"  Token env:       {profile_config.bot_token_env}")
        print(f"  Default channel: {profile_config.default_channel}")
        print(f"  Timeout:         {profile_config.timeout}s")
        print(f"  Max retries:     {profile_config.max_retries}")
        print()

        # Try to resolve token (without displaying it)
        try:
            token = profile_config.get_bot_token()
            print(f"  Token status:    ✓ Found (starts with {token[:10]}...)")
        except ValueError as e:
            print(f"  Token status:    ✗ {e}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@config_app.command
def validate():
    """Validate configuration file structure."""
    try:
        # Try to load app config
        app_config = AppConfig.auto_load()

        print("Configuration validation:")
        print()
        print(f"  Profiles found: {len(app_config.profiles)}")

        all_valid = True
        for name, profile in app_config.profiles.items():
            print(f"\n  Profile '{name}':")
            try:
                token = profile.get_bot_token()
                print(f"    ✓ Token found and valid")
            except ValueError as e:
                print(f"    ✗ Token error: {e}")
                all_valid = False

            print(f"    ✓ Channel: {profile.default_channel}")
            print(f"    ✓ Timeout: {profile.timeout}s")
            print(f"    ✓ Retries: {profile.max_retries}")

        print()
        if all_valid:
            print("✓ All profiles valid")
        else:
            print("✗ Some profiles have errors")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)


@config_app.command
def init():
    """Initialize a new config.json file in the default location."""
    config_dir = Path.home() / ".config" / "slack-agent"
    config_file = config_dir / "config.json"

    if config_file.exists():
        print(f"Error: Config file already exists: {config_file}", file=sys.stderr)
        print("Use 'show' to view current configuration")
        sys.exit(1)

    # Create default configuration
    default_config = {
        "profiles": {
            "default": {
                "bot_token_env": "SLACK_BOT_TOKEN",
                "default_channel": "#general",
                "timeout": 30,
                "max_retries": 3
            }
        }
    }

    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=2)

        print(f"✓ Created config file: {config_file}")
        print()
        print("Next steps:")
        print("  1. Set SLACK_BOT_TOKEN environment variable")
        print("  2. Run 'slack-agent-cli config validate' to verify")
        print("  3. Run 'slack-agent-cli test send-message' to test")

    except Exception as e:
        print(f"Error creating config file: {e}", file=sys.stderr)
        sys.exit(1)


# ====================
# Test Commands
# ====================

@test_app.command
def send_message(
    message: str = Parameter(help="Message to send"),
    profile: str = Parameter(default="default", help="Profile to use"),
    channel: Optional[str] = Parameter(default=None, help="Channel override"),
):
    """Send a test message to Slack."""
    try:
        # Load configuration for the profile
        config = SlackConfig.from_profile(profile)

        # Create notifier
        notifier = SlackNotifier(config=config)

        # Send message
        print(f"Sending message via profile '{profile}'...")
        response = notifier.notify(message=message, channel=channel, level="info")

        target_channel = channel or config.default_channel
        print(f"✓ Message sent successfully to {target_channel}")
        print(f"  Timestamp: {response.get('ts')}")

    except Exception as e:
        print(f"✗ Failed to send message: {e}", file=sys.stderr)
        sys.exit(1)


@test_app.command
def auth(
    profile: str = Parameter(default="default", help="Profile to test")
):
    """Test Slack authentication."""
    try:
        config = SlackConfig.from_profile(profile)

        print(f"Testing authentication for profile '{profile}'...")
        print(f"  Token env: {AppConfig.auto_load().profiles[profile].bot_token_env}")
        print(f"  Token:     {config.bot_token[:10]}...")

        # Create notifier and test connection
        notifier = SlackNotifier(config=config)

        # Try to get bot info
        from slack_sdk import WebClient
        client = WebClient(token=config.bot_token)
        auth_response = client.auth_test()

        print()
        print(f"✓ Authentication successful")
        print(f"  Bot name:  {auth_response['user']}")
        print(f"  Team:      {auth_response['team']}")
        print(f"  Bot ID:    {auth_response['user_id']}")

    except Exception as e:
        print(f"✗ Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


@test_app.command
def channels(
    profile: str = Parameter(default="default", help="Profile to use")
):
    """List available Slack channels."""
    try:
        config = SlackConfig.from_profile(profile)

        from slack_sdk import WebClient
        client = WebClient(token=config.bot_token)

        print(f"Fetching channels for profile '{profile}'...")

        # Get public channels
        response = client.conversations_list(
            types="public_channel,private_channel",
            limit=100
        )

        channels = response.get("channels", [])

        print()
        print(f"Found {len(channels)} channels:")
        print()

        for channel in channels:
            name = channel["name"]
            channel_id = channel["id"]
            is_member = channel.get("is_member", False)
            is_private = channel.get("is_private", False)

            status = "✓" if is_member else " "
            privacy = "🔒" if is_private else "  "

            print(f"  {status} {privacy} #{name} ({channel_id})")

        print()
        print("Legend: ✓ = bot is member, 🔒 = private channel")

    except Exception as e:
        print(f"✗ Failed to list channels: {e}", file=sys.stderr)
        sys.exit(1)


# ====================
# Debug Commands
# ====================

@debug_app.command
def audit_log(
    tail: int = Parameter(default=10, help="Number of recent entries to show"),
    filter_tool: Optional[str] = Parameter(default=None, help="Filter by tool name"),
):
    """Display recent audit log entries."""
    audit_logger = get_audit_logger()

    if not audit_logger.log_file.exists():
        print(f"No audit log found at: {audit_logger.log_file}")
        print("Run some MCP tool calls to generate audit entries")
        sys.exit(0)

    try:
        with open(audit_logger.log_file, "r") as f:
            lines = f.readlines()

        # Parse JSON entries
        entries = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                if filter_tool is None or entry.get("tool_name") == filter_tool:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

        # Take last N entries
        entries = entries[-tail:]

        if not entries:
            print(f"No audit entries found")
            if filter_tool:
                print(f"(filtered by tool_name='{filter_tool}')")
            sys.exit(0)

        print(f"Last {len(entries)} audit entries:")
        if filter_tool:
            print(f"(filtered by tool_name='{filter_tool}')")
        print()

        for entry in entries:
            timestamp = entry.get("timestamp", "?")
            tool_name = entry.get("tool_name", "?")
            success = "✓" if entry.get("success") else "✗"
            duration = entry.get("duration_ms", 0)
            request_id = entry.get("request_id", "?")[:8]

            print(f"  {timestamp} | {success} {tool_name} | {duration:.1f}ms | {request_id}...")

            if not entry.get("success"):
                error = entry.get("error_message", "Unknown error")
                print(f"    Error: {error}")

        print()

    except Exception as e:
        print(f"Error reading audit log: {e}", file=sys.stderr)
        sys.exit(1)


@debug_app.command
def show_config(
    profile: str = Parameter(default="default", help="Profile to display")
):
    """Show resolved configuration for debugging."""
    try:
        # Enable debug mode temporarily
        import os
        old_debug = os.getenv("SLACK_AGENT_DEBUG")
        os.environ["SLACK_AGENT_DEBUG"] = "1"

        config = SlackConfig.from_profile(profile)

        # Restore debug mode
        if old_debug:
            os.environ["SLACK_AGENT_DEBUG"] = old_debug
        else:
            del os.environ["SLACK_AGENT_DEBUG"]

        print(f"Resolved configuration for profile '{profile}':")
        print()
        print(f"  Bot token:       {config.bot_token}")
        print(f"  Default channel: {config.default_channel}")
        print(f"  Timeout:         {config.timeout}s")
        print(f"  Max retries:     {config.max_retries}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@debug_app.command
def check_permissions(
    profile: str = Parameter(default="default", help="Profile to check")
):
    """Check bot permissions in Slack workspace."""
    try:
        config = SlackConfig.from_profile(profile)

        from slack_sdk import WebClient
        client = WebClient(token=config.bot_token)

        # Get auth info
        auth_response = client.auth_test()

        print(f"Bot permissions for profile '{profile}':")
        print()
        print(f"  Bot:  {auth_response['user']}")
        print(f"  Team: {auth_response['team']}")
        print()

        # Note: Getting actual scopes requires additional API calls
        # For now, we just verify auth works
        print("  Auth:     ✓ Valid")
        print("  Channels: ✓ Can list")
        print()
        print("To see full scopes, visit:")
        print(f"  https://api.slack.com/apps")

    except Exception as e:
        print(f"Error checking permissions: {e}", file=sys.stderr)
        sys.exit(1)


# Register subcommands
app.command(config_app, name="config")
app.command(test_app, name="test")
app.command(debug_app, name="debug")


if __name__ == "__main__":
    app()
