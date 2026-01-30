# Development Guide

This guide covers setup, testing, and debugging for slack-agent development.

## Quick Start

### Prerequisites

- Python 3.8+
- pip or poetry
- A Slack workspace with bot creation permissions

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/slack-agent.git
cd slack-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev,test]"
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Slack bot token
```

## Configuration

### Using Direct Environment Variables (Simple)

For testing or simple setups:

```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_DEFAULT_CHANNEL="#general"
```

### Using Profile Configuration (Recommended)

For multi-workspace or production setups:

1. Create config directory:
```bash
mkdir -p ~/.config/slack-agent
```

2. Create `~/.config/slack-agent/config.json`:
```json
{
  "profiles": {
    "default": {
      "bot_token_env": "SLACK_BOT_TOKEN",
      "default_channel": "#general",
      "timeout": 30,
      "max_retries": 3
    },
    "work": {
      "bot_token_env": "SLACK_WORK_BOT_TOKEN",
      "default_channel": "#team-updates",
      "timeout": 30,
      "max_retries": 3
    }
  }
}
```

3. Set environment variables for each profile:
```bash
export SLACK_BOT_TOKEN="xoxb-default-token"
export SLACK_WORK_BOT_TOKEN="xoxb-work-token"
```

4. Validate configuration:
```bash
slack-agent-cli config validate
```

## Running Tests

### Unit Tests

Run all unit tests:
```bash
pytest tests/unit/
```

Run with coverage:
```bash
pytest tests/unit/ --cov=src/slack_notifications --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_config.py -v
```

### Integration Tests

Integration tests require valid Slack credentials:

```bash
pytest tests/integration/ -v
```

Skip integration tests:
```bash
pytest tests/ -m "not integration"
```

### Coverage Targets

- Core modules (config, notifier): 100%
- MCP server: 90%+
- CLI: 80%+
- Overall: 85%+

Current coverage:
```bash
pytest --cov=src/slack_notifications --cov-report=term-missing
```

## Debugging

### Verbose Logging

Enable debug output:
```bash
export SLACK_AGENT_VERBOSE=1
python -m slack_notifications.mcp_server
```

### Credential Masking

By default, credentials are masked in logs. To disable (development only):
```bash
export SLACK_AGENT_DEBUG=1
```

### Audit Log

View recent tool calls:
```bash
slack-agent-cli debug audit-log --tail 20
```

Filter by tool:
```bash
slack-agent-cli debug audit-log --filter send_slack_message
```

View full audit log:
```bash
tail -f ~/.config/slack-agent/audit.log
```

### Testing Slack Connection

Send a test message:
```bash
slack-agent-cli test send-message "Hello from slack-agent" --channel "#test"
```

Test authentication:
```bash
slack-agent-cli test auth
```

List available channels:
```bash
slack-agent-cli test channels
```

## Adding New MCP Tools

### 1. Define the Tool Function

Add to `src/slack_notifications/mcp_server.py`:

```python
@mcp.tool()
def my_new_tool(
    param1: str,
    param2: Optional[str] = None
) -> Dict[str, Any]:
    """
    Brief description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Structured response with status, data, and request_id
    """
    request_id = set_request_id()
    audit_logger = get_audit_logger()
    start_time = audit_logger.start_timer()
    
    try:
        # Your implementation
        result = do_something(param1, param2)
        duration_ms = audit_logger.stop_timer(start_time)
        
        audit_logger.log_tool_call(
            tool_name="my_new_tool",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=True,
            duration_ms=duration_ms,
        )
        
        return {
            "status": "success",
            "data": result,
            "request_id": request_id,
        }
    except Exception as e:
        error_msg = mask_credentials(str(e))
        duration_ms = audit_logger.stop_timer(start_time)
        
        audit_logger.log_tool_call(
            tool_name="my_new_tool",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=False,
            error_message=error_msg,
            duration_ms=duration_ms,
        )
        
        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id,
        }
    finally:
        clear_request_id()
```

### 2. Update Agent Instructions

Add to `docs/system-prompts/agent-instructions.md`:
- Clear description of what the tool does
- Example usage scenarios
- Common error modes

### 3. Add Tests

Create unit test in `tests/unit/test_mcp_server.py`:

```python
def test_my_new_tool(mock_config):
    """Test my_new_tool."""
    from slack_notifications.mcp_server import my_new_tool
    
    result = my_new_tool("test_param1")
    
    assert result["status"] == "success"
    assert "request_id" in result
```

## Running the MCP Server

### Development

```bash
python -m slack_notifications.mcp_server
```

With verbose logging:
```bash
SLACK_AGENT_VERBOSE=1 python -m slack_notifications.mcp_server
```

### With Claude Desktop

Add to Claude Desktop config file:

**macOS/Linux:** `~/.config/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "slack-notifications": {
      "command": "python",
      "args": ["-m", "slack_notifications.mcp_server"]
    }
  }
}
```

## Code Style

### Formatting

Run black:
```bash
black src/ tests/
```

Run isort:
```bash
isort src/ tests/
```

### Linting

Run flake8:
```bash
flake8 src/ tests/
```

Run mypy:
```bash
mypy src/
```

### Pre-commit Hook

Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

## Common Issues

### Token Not Found

Error: `Bot token not found in environment variable: SLACK_BOT_TOKEN`

**Solution:**
- Check `.env` file is loaded: `echo $SLACK_BOT_TOKEN`
- Verify environment variable is set: `env | grep SLACK`
- For profile configuration: `slack-agent-cli config show`

### Permission Denied

Error: `Error: the user is not allowed to access this resource`

**Solution:**
- Verify bot token is valid
- Check bot has required permissions: `slack-agent-cli test auth`
- Verify channel exists and bot is a member: `slack-agent-cli test channels`

### Audit Log Permission Error

Error: `Permission denied: ~/.config/slack-agent/audit.log`

**Solution:**
- Verify directory exists: `mkdir -p ~/.config/slack-agent`
- Check directory permissions: `ls -la ~/.config/slack-agent`
- Clear old log if needed: `rm ~/.config/slack-agent/audit.log`

See [troubleshooting.md](troubleshooting.md) for more issues.

## Making a Contribution

1. Create a feature branch
2. Make changes and add tests
3. Run test suite: `pytest tests/`
4. Run linters: `black src/ tests/ && isort src/ tests/ && flake8 src/`
5. Check types: `mypy src/`
6. Create pull request

See CONTRIBUTING.md for more details.
