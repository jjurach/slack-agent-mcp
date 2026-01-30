# MCP Technology Standards

**Version:** 1.0
**Last Updated:** 2026-01-30
**Synced from:** slack-agent
**Status:** Active across all MCP projects

This document defines the standard technology combinations used across all MCP projects (slack-agent, google-personal-mcp, and future projects), enabling consistent patterns and easy knowledge transfer between projects.

## Core Technology Stack

### MCP Server Framework: FastMCP

- **Choice:** FastMCP (from Anthropic's mcp library)
- **Why:** Type-safe tool definitions, async/await native, minimal boilerplate
- **When:** All MCP servers in this ecosystem
- **Not:** Litestar, FastAPI, custom implementations

```python
from fastmcp import FastMCP

mcp = FastMCP("service-name", instructions="Brief description")

@mcp.tool()
def my_tool(param: str) -> dict:
    """Tool description."""
    return {"status": "success", "data": result, "request_id": request_id}
```

### Configuration: Pydantic + python-dotenv

- **Choice:** Pydantic for validation + python-dotenv for .env loading
- **Why:** Type-safety at load time, clear error messages, works with environment variables
- **Pattern:** Load .env → parse into Pydantic models → use models throughout app
- **When:** All configuration management in MCP projects
- **Fallback:** Plain environment variables if no config file

```python
from pydantic import BaseModel, Field

class ProfileConfig(BaseModel):
    api_token_env: str
    default_resource: str = "default"
    timeout: int = Field(default=30, ge=1, le=300)
```

### CLI Framework: cyclopts

- **Choice:** cyclopts for type-driven CLI
- **Why:** Generates help from type hints, subcommand support, modern Python
- **When:** All MCP projects should have diagnostic CLI
- **Not:** Click, argparse, typer (cyclopts is more Pythonic)

```python
from cyclopts import App

app = App(name="service-cli")
config_app = App(name="config")

@config_app.command
def show(profile: str = "default"):
    """Show profile configuration."""
    # Implementation

app.command(config_app, name="config")
```

### Testing: pytest + pytest-cov

- **Choice:** pytest with fixtures + pytest-cov for coverage
- **Why:** Modern framework, excellent fixtures, built-in parametrization
- **Mocking:** unittest.mock (stdlib) for services
- **When:** All MCP projects
- **Markers:** @pytest.mark.integration for tests requiring real credentials

```python
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_service():
    service = MagicMock()
    service.do_work.return_value = {"status": "ok"}
    return service

def test_something(mock_service):
    """Test behavior."""
    assert mock_service.do_work() == {"status": "ok"}
```

### Logging: Python logging + JSON structured logs

- **Choice:** stdlib logging with optional JSON output
- **Why:** No external dependencies, works with all log aggregation services
- **Pattern:** Basic text for development, JSON for production
- **Sanitization:** Mask credentials automatically using regex patterns
- **Location:** `~/.config/{service}/audit.log` for audit trails

### Async: asyncio

- **Choice:** asyncio natively (all FastMCP tools are async)
- **Why:** FastMCP is async-native, no external dependencies needed
- **Pattern:** All I/O operations async, request handling natively async
- **When:** FastMCP-based servers (always async)

## Standard Directory Structure

Every MCP project follows this structure:

```
project-mcp/
├── src/
│   ├── service_mcp/                  # MCP server entry point
│   │   ├── __init__.py
│   │   └── mcp_server.py             # FastMCP server, tool definitions
│   │
│   └── service_core/                 # Reusable libraries
│       ├── __init__.py
│       ├── config.py                 # Configuration + Pydantic models
│       ├── service.py                # Main service class
│       ├── cli.py                    # CLI commands (cyclopts)
│       ├── logging/                  # Logging utilities
│       │   ├── __init__.py
│       │   ├── audit.py              # Audit logging
│       │   └── structured.py         # JSON logging
│       └── utils/                    # Utilities
│           ├── __init__.py
│           ├── context.py            # Request context (ID, audit trail)
│           └── sanitizer.py          # Credential masking

├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── unit/                         # Fast tests, all mocked
│   │   ├── test_config.py
│   │   ├── test_service.py
│   │   └── test_mcp_server.py
│   └── integration/                  # Real credentials required
│       └── test_service_integration.py

├── docs/
│   ├── mcp-implementation-guide.md   # Service-specific patterns
│   ├── development-guide.md
│   ├── troubleshooting.md
│   └── system-prompts/
│       ├── mcp-standards.md          # This file (shared)
│       └── agent-instructions.md     # Service-specific tools

├── pytest.ini
├── .coveragerc
├── pyproject.toml
├── .env.example
├── README.md
└── CONTRIBUTING.md
```

## Standard Dependencies

### Required

```
mcp>=0.1.0
pydantic>=2.5.0
python-dotenv>=1.0.0
cyclopts>=2.0.0
```

### Development/Testing

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
black
isort
flake8
mypy
```

### Optional Based on Service Type

```
# For Google APIs:
google-api-python-client
google-auth-oauthlib

# For Slack APIs:
slack-sdk>=3.25.0

# For AWS APIs:
boto3

# For logging:
python-json-logger
```

## Standard Patterns

### 1. Request ID Context Management

All tool calls should include request ID tracking for debugging:

```python
from slack_notifications.utils import set_request_id, get_request_id, clear_request_id

@mcp.tool()
def tool_name(param: str) -> dict:
    request_id = set_request_id()
    try:
        # Do work
        return {"status": "success", "data": result, "request_id": request_id}
    finally:
        clear_request_id()
```

### 2. Service Locator Pattern

```python
def get_service(profile: str = "default") -> ServiceClass:
    """Get service instance with credentials."""
    config = config_manager.get_profile(profile)
    return ServiceClass(config)
```

### 3. Structured Tool Response

Every tool returns consistent structure:

```python
{
    "status": "success" | "error",
    "data": {...},  # On success
    "message": "...",  # On error
    "request_id": "uuid-here"
}
```

### 4. Audit Logging

Log all tool calls:

```python
from logging import get_audit_logger

audit_logger = get_audit_logger()
audit_logger.log_tool_call(
    tool_name="send_message",
    parameters={"message": msg},
    request_id=request_id,
    success=True,
    duration_ms=elapsed
)
```

### 5. Configuration Validation with Pydantic

```python
class ProfileConfig(BaseModel):
    api_token_env: str
    resource_id: Optional[str] = None
    timeout: int = Field(default=30, ge=1, le=300)

    @validator('api_token_env')
    def validate_env_var(cls, v):
        if not os.getenv(v):
            raise ValueError(f"Environment variable {v} not set")
        return v
```

### 6. CLI Command Pattern

```python
from cyclopts import App

app = App(name="service-cli")
config_app = App(name="config")

@config_app.command
def list_resources(profile: str = "default"):
    """List available resources for a profile."""
    config = AppConfig.auto_load()
    for name, config in config.profiles[profile].items():
        print(f"{name}: {config}")

app.command(config_app, name="config")
```

### 7. Test Fixture Pattern

```python
@pytest.fixture
def mock_service():
    """Mock service with predefined responses."""
    service = MagicMock()
    service.do_work.return_value = {"status": "ok"}
    return service

@pytest.fixture
def valid_config():
    """Valid configuration for testing."""
    return AppConfig(
        profiles={
            "default": ProfileConfig(api_token_env="TEST_TOKEN")
        }
    )

def test_tool(mock_service, valid_config):
    """Test tool behavior."""
    assert mock_service.do_work() == {"status": "ok"}
```

## Environment Variables Convention

Every MCP project supports these standard environment variables:

```bash
# Configuration
${PROJECT}_CONFIG              # Path to config.json
${PROJECT}_PROFILE             # Active profile (default: "default")

# Behavior Control
${PROJECT}_VERBOSE             # Enable verbose logging (0|1)
${PROJECT}_JSON_LOGS           # Use JSON logging format (0|1)
${PROJECT}_DEBUG               # Disable credential masking (0|1)

# Service-Specific
# (Add your own, e.g., SLACK_MCP_TIMEOUT, GOOGLE_MCP_MAX_RETRIES)
```

For slack-agent specifically:
- `SLACK_AGENT_CONFIG` - Path to config.json
- `SLACK_AGENT_PROFILE` - Active profile name
- `SLACK_AGENT_VERBOSE` - Verbose logging
- `SLACK_AGENT_JSON_LOGS` - JSON logging format
- `SLACK_AGENT_DEBUG` - Disable masking

## Coverage Targets

All projects target:
- **Core modules:** 100%
- **MCP server:** 90%+
- **CLI:** 80%+
- **Overall:** 85%+

Run: `pytest --cov=src --cov-report=html`

## Sync Protocol

When adopting these standards in a new MCP project:

1. Copy this document to `docs/system-prompts/mcp-standards.md` **unchanged**
2. Create service-specific implementation guide (`docs/mcp-implementation-guide.md`)
3. Copy standard directory structure as template
4. Copy standard dependencies to pyproject.toml
5. Update environment variables for your service
6. Copy this document as-is; all changes go in project-specific files

### Version Tracking

Each project tracks:
```
docs/system-prompts/mcp-standards.md
- Synced from: google-personal-mcp (source of truth)
- Last synced: 2026-01-30
- Local changes: None (should be exact copy)
```

## When to Deviate

Deviations require team consensus:

- **Never deviate from:** FastMCP, Pydantic, cyclopts, pytest
- **Can adapt:** Logging output format, audit log location
- **Can add:** Service-specific tools, profiles, validation
- **Document:** Any deviation in project-specific implementation guide

## Key Benefits

This standardization enables:

- ✅ **Consistency:** All MCP servers behave similarly
- ✅ **Knowledge Transfer:** Engineers learn once, apply everywhere
- ✅ **Maintainability:** Same patterns across all projects
- ✅ **Testing:** Reusable test fixtures and patterns
- ✅ **Observability:** Consistent logging and audit trails
- ✅ **Documentation:** Portable documentation syncs across projects

