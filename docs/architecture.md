# System Architecture

This document describes the architecture of the Slack Notifications project.

## High-Level Architecture

The slack-agent project consists of three main components:

```
┌──────────────────────────────────────────────────────────┐
│           User Applications / AI Agents                  │
└──────────┬───────────────────────────────────────────────┘
           │
     ┌─────┴──────────────────────────────────┐
     │                                        │
     ▼                                        ▼
┌──────────────────────┐         ┌──────────────────────┐
│ slack-notifications  │         │   slack-mcp-server   │
│    (Python lib)      │         │  (FastMCP server)    │
│  - SlackNotifier     │         │  - MCP Tools         │
│  - Configuration     │         │  - Tool wrappers     │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                │
           │                                │
           ├────────────────┬───────────────┤
           │                │               │
           ▼                ▼               ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────┐
      │ SlackClient  │  │ slack-agent  │  │ Config   │
      │ (Slack API)  │  │  (RTM bot)   │  │ Manager  │
      └──────────────┘  └──────────────┘  └──────────┘
           │                │
           └────────┬───────┘
                    │
                    ▼
            ┌────────────────┐
            │  Slack API     │
            │ (External SaaS)│
            └────────────────┘
```

## Project Structure

```
slack-agent/
├── src/
│   ├── slack_notifications/       # Core notification library
│   │   ├── __init__.py           # Public API exports
│   │   ├── client.py             # Slack API client wrapper
│   │   ├── config.py             # Configuration management
│   │   ├── exceptions.py         # Custom exception types
│   │   ├── notifier.py           # Main SlackNotifier class
│   │   ├── mcp_server.py         # FastMCP server implementation
│   │   └── py.typed              # PEP 561 type hints marker
│   ├── slack_agent/              # Slack bot agent
│   │   ├── __init__.py
│   │   └── __main__.py           # RTM-based time query bot
│   └── slack_mcp_server/         # Deprecated: kept for compatibility
├── tests/                         # Pytest test suite
├── examples/                      # Example configurations
├── docs/                          # Project documentation
├── dev_notes/                     # Development planning and logs
├── pyproject.toml                 # Project metadata and dependencies
└── README.md                      # Project overview
```

## Core Components

### 1. slack-notifications Library

**Purpose:** Provides Python API for sending Slack notifications

**Key Classes:**
- `SlackNotifier` - Main class for sending messages
- `SlackClient` - Low-level Slack API wrapper
- `Config` - Configuration loader (env/file/defaults)

**Key Features:**
- Async and sync notification methods
- Custom levels (info, success, warning, error)
- Channel-specific routing
- Retry logic with exponential backoff
- Type hints for IDE support

**Configuration:** Via environment variables, .env file, or TOML config

### 2. slack-mcp-server (FastMCP)

**Purpose:** Exposes slack-notifications as Model Context Protocol tools for AI agents

**Key Features:**
- MCP-compliant tool interface
- Tools for sending messages, success, warning, error notifications
- Configuration tool for runtime setup
- Integrates with AI agent frameworks

**Entry Point:** `slack_mcp_server.py` or command `python -m slack_notifications.mcp_server`

### 3. slack-agent (RTM Bot)

**Purpose:** Real-time Slack monitoring bot that responds to queries

**Key Features:**
- RTM (Real Time Messaging) API for instant message processing
- Time query responses (current CST time)
- Timestamped logging for monitoring
- Channel discovery and monitoring
- Configurable channel filtering

**Entry Point:** `python -m slack_agent` or `slack_agent/__main__.py`

## Data Flow

### Notification Flow

```
User Code
    │
    ├─→ notify_milestone(msg, channel, level)
    │
    ▼
SlackNotifier.notify()
    │
    ├─→ SlackClient.send_message()
    │
    ▼
HTTP POST → Slack API
    │
    ▼
Slack Channel
```

### MCP Server Flow

```
AI Agent
    │
    ├─→ MCP Tool Call: send_slack_message()
    │
    ▼
FastMCP Server
    │
    ├─→ Tool Handler Function
    │
    ▼
SlackNotifier.notify()
    │
    ▼
Slack Channel
```

### RTM Agent Flow

```
Slack Channel (RTM)
    │
    ├─→ Message Event
    │
    ▼
slack-agent (RTM Connection)
    │
    ├─→ Pattern Match (time query?)
    │
    ├─→ YES: Format response
    │
    ▼
SlackClient.send_message()
    │
    ▼
Slack Channel (Reply)
```

## External Dependencies

### Required
- **slack-sdk** - Official Slack Python SDK for API and RTM
- **pydantic** - Data validation and settings management
- **python-dotenv** - .env file support
- **fastmcp** - Model Context Protocol server implementation

### Optional (Development)
- **pytest** - Testing framework
- **black** - Code formatter
- **isort** - Import sorter
- **flake8** - Linter
- **mypy** - Type checker
- **pre-commit** - Git hooks framework

## Configuration Management

Configuration is loaded in priority order (highest to lowest):

1. **Environment Variables** - `SLACK_*` prefix
2. **.env File** - `python-dotenv` loader
3. **TOML File** - `slack_notifications.toml`
4. **Defaults** - Built-in fallbacks

Key configurations:
- `SLACK_BOT_TOKEN` - Bot OAuth token (required)
- `SLACK_DEFAULT_CHANNEL` - Default notification channel
- `SLACK_TIMEOUT` - API request timeout
- `SLACK_MAX_RETRIES` - Retry count

## Error Handling

**Exception Hierarchy:**
- `SlackNotificationError` - Base exception for all slack-notifications errors
- Subtypes for specific failures (API errors, config errors, etc.)

**Error Handling Strategy:**
- Retry on transient failures (rate limits, timeouts)
- Log all errors with context
- Raise exceptions for application handling
- Async methods preserve error propagation

## Testing Strategy

**Test Organization:**
- `tests/` - Unit and integration tests using pytest
- Fixtures for mocking Slack API responses
- Configuration test fixtures

**Coverage:** Aim for >80% code coverage

**Test Patterns:**
- Mock `slack_sdk.WebClient` for unit tests
- Integration tests with test Slack workspace (optional)
- Configuration tests with temp files

## Deployment Considerations

### As Library
- Published to PyPI as `slack-notifications`
- Consumed via `pip install slack-notifications`
- No external services required beyond Slack API

### As MCP Server
- Can run as standalone process
- Integrates with AI agent frameworks
- Environment configuration via env vars
- No additional infrastructure needed

### As Slack Agent
- Runs as foreground process
- Monitors RTM connection continuously
- Handles reconnection on network failures
- Suitable for containerized deployment (Docker)

## Security Architecture

**Token Management:**
- Bot token stored in environment variables or .env file
- Never hardcoded or logged
- .env file excluded from git

**API Access:**
- Uses official Slack SDK with OAuth
- Respects Slack API rate limits
- Implements exponential backoff on rate limiting

**Logging:**
- No sensitive data (tokens) in logs
- Message content may be logged (consider privacy)
- Timestamps in CST for timezone clarity

## Agent Kernel Integration

This project integrates with the **Agent Kernel** for:
- Development workflow (see [AGENTS.md](../AGENTS.md))
- Definition of Done criteria (see [docs/definition-of-done.md](definition-of-done.md))
- Project-specific guidelines (see [docs/mandatory.md](mandatory.md))

## See Also

- [Implementation Reference](implementation-reference.md) - Code patterns and examples
- [Definition of Done](definition-of-done.md) - Quality checklist
- [AGENTS.md](../AGENTS.md) - Development workflow
- [Slack Agent Usage Guide](slack-agent-usage.md) - RTM agent documentation
- [MCP Service Setup](mcp-service-setup.md) - FastMCP server setup
- [Slack API Setup](slack-api-setup.md) - Slack app configuration

---
Last Updated: 2026-01-29
