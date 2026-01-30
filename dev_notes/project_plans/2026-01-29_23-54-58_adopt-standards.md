# Project Plan: Adopt google-personal-mcp Standards for slack-agent

**Created:** 2026-01-29 23:54:58
**Status:** Draft
**Related Spec:** `dev_notes/inbox/adopt-standards.md`

## Overview

This plan adopts best practices from the `google-personal-mcp` project into `slack-agent` across four key areas: MCP serving architecture, debugging/troubleshooting infrastructure, configuration/env/command-line options, and secrets management. The goal is to modernize slack-agent with proven patterns while maintaining compatibility.

**Critical Addition (Per User Requirements):**
This plan includes a comprehensive documentation standardization effort (**Phase 5.5**) that creates **portable, sharable documentation** (`docs/system-prompts/mcp-standards.md` and `docs/mcp-project-sync.md`) designed to be manually synced across all MCP projects (slack-agent, google-personal-mcp, etc.). This enables:
- **Single source of truth** for MCP technology choices across the ecosystem
- **Agentic instruction frameworks** that agents can apply to new MCP servers
- **Consistent patterns** that agents can learn once and apply everywhere
- **Easy onboarding** of new MCP projects following established standards

## Analysis Summary

After comparing slack-agent with google-personal-mcp, the following areas show significant opportunities for improvement:

### Current State: slack-agent
- **MCP Server**: Basic FastMCP implementation with 5 tools, minimal error handling
- **Configuration**: Single config.py with environment variable loading, no profile support
- **Debugging**: Basic logging via Python logging module, no audit trail
- **CLI**: No CLI tools for testing/diagnostics
- **Testing**: Basic pytest setup, no integration tests
- **Documentation**: Minimal, no troubleshooting guide
- **Secrets**: Environment variables only, no file-based credentials

### Target State: google-personal-mcp Patterns
- **MCP Server**: Request ID tracking, audit logging, structured responses, credential masking
- **Configuration**: Profile-based config, Pydantic validation, XDG compliance, .env support
- **Debugging**: Verbose logging flags, JSON logs, audit trail, component testing scripts
- **CLI**: Full CLI with subcommands (config, test, debug), cyclopts framework
- **Testing**: Unit tests with mocks, integration tests, coverage reporting
- **Documentation**: Development guide, troubleshooting guide, implementation reference
- **Secrets**: File-based + env-based, profile isolation, credential masking in logs

## Phase 1: Core Infrastructure Improvements

### 1.1 Request ID Tracking and Context Management

**Goal:** Add request ID tracking to all MCP tool calls for debugging and audit trails.

**Files to Create:**
- `src/slack_notifications/utils/__init__.py`
- `src/slack_notifications/utils/context.py` - Request ID management (set, get, clear)

**Implementation:**
```python
# context.py pattern from google-personal-mcp
import contextvars
import uuid

_request_id_var = contextvars.ContextVar('request_id', default=None)

def set_request_id() -> str:
    request_id = str(uuid.uuid4())
    _request_id_var.set(request_id)
    return request_id

def get_request_id() -> str:
    return _request_id_var.get()

def clear_request_id():
    _request_id_var.set(None)
```

**Files to Modify:**
- `src/slack_notifications/mcp_server.py` - Add request_id to all tool responses

### 1.2 Audit Logging Infrastructure

**Goal:** Track all MCP tool calls with success/failure status, parameters, and timing.

**Files to Create:**
- `src/slack_notifications/logging/__init__.py`
- `src/slack_notifications/logging/audit.py` - AuditLogger class
- `src/slack_notifications/logging/structured.py` - JSON logging support

**Implementation:**
- Audit log location: `~/.config/slack-agent/audit.log`
- Log format: JSON with timestamp, tool_name, parameters, success, error_message, request_id
- Environment control: `SLACK_MCP_VERBOSE`, `SLACK_MCP_JSON_LOGS`, `SLACK_MCP_DEBUG`

**Files to Modify:**
- `src/slack_notifications/mcp_server.py` - Add audit logging to each tool

### 1.3 Credential Sanitization

**Goal:** Prevent Slack tokens and sensitive data from appearing in logs.

**Files to Create:**
- `src/slack_notifications/utils/sanitizer.py` - Credential masking utilities

**Implementation:**
```python
# Patterns to mask:
# - Slack bot tokens: xoxb-*
# - Slack user tokens: xoxp-*
# - Slack webhook URLs
# Environment control: SLACK_MCP_DEBUG (when true, disables masking)
```

**Files to Modify:**
- `src/slack_notifications/logging/audit.py` - Mask credentials in audit logs
- `src/slack_notifications/mcp_server.py` - Mask credentials in error responses

### 1.4 Enhanced Error Handling with Structured Responses

**Goal:** All tools return consistent `{status, data/message, request_id}` structure.

**Files to Modify:**
- `src/slack_notifications/mcp_server.py` - Refactor all tools to return structured responses
- Add try/except/finally pattern with request_id management
- Ensure tools never raise exceptions to MCP layer

**Pattern:**
```python
@mcp.tool()
def send_slack_message(...) -> dict:
    request_id = set_request_id()
    try:
        # operation
        audit_logger.log_tool_call(...)
        return {"status": "success", "data": result, "request_id": request_id}
    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)
        audit_logger.log_tool_call(..., success=False, error_message=error_msg)
        return {"status": "error", "message": error_msg, "request_id": request_id}
    finally:
        clear_request_id()
```

## Phase 2: Configuration Enhancements

### 2.1 Profile-Based Configuration

**Goal:** Support multiple Slack workspaces/tokens via profile system.

**Files to Create:**
- `~/.config/slack-agent/config.json` - Profile configuration
- `~/.config/slack-agent/profiles/default/` - Default profile directory

**Configuration Structure:**
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

**Files to Modify:**
- `src/slack_notifications/config.py` - Add profile support, XDG compliance

### 2.2 Pydantic Configuration Validation

**Goal:** Type-safe configuration with automatic validation.

**Files to Modify:**
- `src/slack_notifications/config.py` - Convert to Pydantic models

**Implementation:**
```python
from pydantic import BaseModel, Field, validator

class ProfileConfig(BaseModel):
    bot_token_env: str
    default_channel: str = "#general"
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)

    @validator('default_channel')
    def validate_channel(cls, v):
        if not (v.startswith('#') or v.startswith('@')):
            raise ValueError("Channel must start with # or @")
        return v

class AppConfig(BaseModel):
    profiles: Dict[str, ProfileConfig]
```

### 2.3 Enhanced .env File Support

**Goal:** Support .env file loading with profile-specific variables.

**Files to Modify:**
- `src/slack_notifications/config.py` - Add python-dotenv integration
- `.env.example` - Document profile-based environment variables

**Dependencies to Add:**
- `python-dotenv`

### 2.4 Environment-Based Configuration Override

**Goal:** Allow configuration path override via environment variables.

**Environment Variables:**
- `SLACK_AGENT_CONFIG` - Path to config.json
- `SLACK_AGENT_PROFILE` - Active profile name (default: "default")
- `SLACK_AGENT_VERBOSE` - Enable verbose logging
- `SLACK_AGENT_JSON_LOGS` - Enable JSON logging
- `SLACK_AGENT_DEBUG` - Disable credential masking

## Phase 3: CLI and Developer Tools

### 3.1 CLI Framework (cyclopts)

**Goal:** Add CLI for testing, diagnostics, and configuration management.

**Files to Create:**
- `src/slack_notifications/cli.py` - CLI command definitions

**Dependencies to Add:**
- `cyclopts` - Modern type-driven CLI framework

**CLI Structure:**
```bash
slack-agent config list-profiles
slack-agent config show [--profile default]
slack-agent config validate
slack-agent test send-message "test message" [--profile default] [--channel #test]
slack-agent debug check-auth [--profile default]
slack-agent debug audit-log [--tail 10] [--filter tool_name]
```

**Files to Modify:**
- `pyproject.toml` - Add `slack-agent` CLI entry point

### 3.2 Configuration CLI Commands

**Goal:** Manage configuration without editing JSON files.

**Commands:**
- `config list-profiles` - List available profiles
- `config show` - Display profile configuration
- `config validate` - Validate config.json structure
- `config test-token` - Verify Slack token validity

### 3.3 Testing CLI Commands

**Goal:** Test Slack integration without MCP server.

**Commands:**
- `test send-message` - Send test message to channel
- `test auth` - Test authentication
- `test channels` - List available channels

### 3.4 Debugging CLI Commands

**Goal:** Troubleshoot issues and inspect logs.

**Commands:**
- `debug audit-log` - Query audit log
- `debug show-config` - Show resolved configuration
- `debug check-permissions` - Verify bot permissions

## Phase 4: Testing Infrastructure

### 4.1 Test Organization and Fixtures

**Goal:** Comprehensive testing with proper mocking.

**Files to Create:**
- `tests/conftest.py` - Shared pytest fixtures
- `tests/unit/test_config.py` - Configuration tests
- `tests/unit/test_notifier.py` - Notifier tests with mocks
- `tests/unit/test_mcp_server.py` - MCP tool tests
- `tests/integration/test_slack_integration.py` - Real Slack API tests

**Fixtures:**
```python
@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient."""
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1234567890.123456"}
    return mock_client

@pytest.fixture
def mock_config():
    """Mock SlackConfig."""
    return SlackConfig(
        bot_token="xoxb-test-token",
        default_channel="#test",
        timeout=30,
        max_retries=3
    )
```

### 4.2 Unit Tests with Mocking

**Goal:** Fast, deterministic tests without API calls.

**Test Coverage:**
- Configuration loading and validation
- Credential masking
- Request ID management
- Audit logging
- MCP tool parameter validation
- Error handling

### 4.3 Integration Tests

**Goal:** End-to-end tests with real Slack API.

**Requirements:**
- Skip if `SLACK_BOT_TOKEN` not set
- Use `@pytest.mark.integration` marker
- Test against real test channel

**Tests:**
- Authentication flow
- Message sending
- Error handling with invalid tokens
- Channel permissions

### 4.4 Coverage Reporting

**Goal:** Track test coverage with targets.

**Configuration:**
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --cov=src/slack_notifications
    --cov-report=term-missing
    --cov-report=html
```

**Coverage Targets:**
- Core modules (config, notifier, client): 100%
- MCP server: 90%+
- CLI: 80%+
- Overall: 85%+

## Phase 5: Documentation

### 5.1 Development Guide

**Goal:** Document development workflow, debugging, and contributing.

**Files to Create:**
- `docs/development-guide.md` - Setup, testing, debugging
- `docs/troubleshooting.md` - Common issues and solutions

**Content:**
- Development environment setup
- Running tests
- Adding new MCP tools
- Debugging techniques (verbose logging, audit log inspection)
- Common issues and fixes

### 5.2 Implementation Reference

**Goal:** Document code patterns and best practices.

**Files to Create:**
- `docs/implementation-reference.md` - Patterns for features, testing, CLI

**Content:**
- MCP tool development pattern
- Configuration pattern
- CLI command pattern
- Testing pattern
- Logging pattern

### 5.3 Troubleshooting Guide

**Goal:** Help users diagnose and fix common problems.

**Files to Modify:**
- `docs/troubleshooting.md`

**Content:**
- Token not found errors
- Permission denied errors
- Channel not found errors
- Network timeout issues
- Configuration validation errors
- Debugging checklist

### 5.4 README Updates

**Goal:** Update README with new CLI and configuration features.

**Files to Modify:**
- `README.md` - Add CLI documentation, profile configuration examples

## Phase 5.5: Standardized MCP Implementation Guide (Portable)

**Goal:** Create a comprehensive MCP implementation guide specific to slack-agent that documents technology choices, patterns, and architecture in a way that can be manually synced across all MCP projects.

**Files to Create:**
- `docs/mcp-implementation-guide.md` - **Master document** (modeled after google-personal-mcp's guide, but adapted for Slack)
- `docs/system-prompts/mcp-standards.md` - Technology combinations and agentic instruction framework
- `docs/mcp-project-sync.md` - Guide for syncing this documentation to other MCP projects

### 5.5.1 MCP Implementation Guide for slack-agent

**Content Structure (Modeled on google-personal-mcp):**

1. **Core Architecture**
   - FastMCP server foundation
   - Service-oriented design (MCP layer → Service layer → Slack API)
   - Request ID context management
   - Audit logging integration

2. **Technology Stack & Rationale**
   - Why FastMCP (vs. Litestar/FastAPI)
   - Why Slack SDK (vs. raw HTTP)
   - Why Pydantic (vs. ConfigParser/JSON schema validators)
   - Why cyclopts (vs. Click/argparse)
   - Why pytest with pytest-cov (vs. unittest/coverage.py)
   - Why python-dotenv (vs. environment-only configuration)

3. **Configuration System**
   - Profile-based credential storage (patterns applicable to any credential type)
   - Directory structure: `~/.config/slack-agent/`
   - `config.json` - Resource aliases and profile mapping
   - `.env` files - Sensitive values
   - Environment variable overrides
   - Pydantic validation at load time

4. **Authentication & Secrets Management**
   - Token storage patterns (file-based, environment-based)
   - Credential masking in logs
   - Scope/permission limitation (Slack token permissions)
   - Access control at service layer (what this bot can do)
   - Audit trails for credential usage

5. **Directory Structure & Rationale**
   - `src/slack_notifications/` - MCP server package
   - `src/slack_notifications_core/` - Reusable libraries (can be used by CLI, scripts, other projects)
   - `tests/` - Parallel structure to src
   - `docs/system-prompts/` - Agentic instruction templates

6. **Testing Strategy**
   - Unit tests with service mocking
   - Integration tests with real Slack workspace
   - Fixtures for common scenarios
   - Test markers (@pytest.mark.integration)
   - Coverage targets per component

7. **Logging & Observability**
   - Structured audit logging (JSON format for parsing)
   - Request ID propagation through call chains
   - Verbose logging control via environment variable
   - Secrets sanitization patterns
   - Log aggregation recommendations

8. **CLI Integration**
   - Cyclopts framework benefits
   - Command structure: config, test, debug subcommands
   - Bridging CLI and MCP server (shared service layer)
   - Using CLI for development and troubleshooting

9. **Best Practices & Patterns**
   - Service Locator pattern (get_slack_client)
   - Context object pattern (RequestContext)
   - Lazy-load service objects
   - Access control at service layer
   - Configuration validation with Pydantic
   - Consistent error handling strategy
   - Environment-driven behavior
   - Reusable service classes

### 5.5.2 Technology Combinations Document

**File:** `docs/system-prompts/mcp-standards.md`

**Purpose:** Define the standard technology combinations used across MCP projects, with explanation of why each combination works well together.

**Content:**

```markdown
# MCP Technology Standards for Consistent Implementation

This document defines the standard technology combinations used across all MCP projects,
enabling consistent patterns and easy knowledge transfer between projects.

## Core Technology Stack

### MCP Server Framework: FastMCP
- **Choice:** FastMCP (from Anthropic's mcp library)
- **Why:** Type-safe tool definitions, async/await native, minimal boilerplate
- **When:** All MCP servers in this ecosystem
- **Not:** Litestar, FastAPI, custom implementations

### Configuration: Pydantic + python-dotenv
- **Choice:** Pydantic for validation + python-dotenv for .env loading
- **Why:** Type-safety at load time, clear error messages, works with environment variables
- **Pattern:** Load .env → parse into Pydantic models → use models throughout app
- **When:** All configuration management in MCP projects
- **Fallback:** Plain environment variables if no config file

### CLI Framework: cyclopts
- **Choice:** cyclopts for type-driven CLI
- **Why:** Generates help from type hints, subcommand support, modern Python
- **When:** All MCP projects should have diagnostic CLI
- **Not:** Click, argparse, typer (cyclopts is more Pythonic)

### Testing: pytest + pytest-cov
- **Choice:** pytest with fixtures + pytest-cov for coverage
- **Why:** Modern framework, excellent fixtures, built-in parametrization
- **Mocking:** unittest.mock (stdlib) for services, requests-mock for HTTP
- **When:** All MCP projects
- **Markers:** @pytest.mark.integration for tests requiring real credentials

### Logging: Python logging + JSON structured logs
- **Choice:** stdlib logging with optional JSON output
- **Why:** No external dependencies, works with all log aggregation services
- **Pattern:** Basic text for development, JSON for production
- **Sanitization:** Mask credentials automatically using regex patterns

### Async: asyncio + anyio
- **Choice:** asyncio with anyio for sync-to-async bridges
- **Why:** asyncio is stdlib, anyio provides compatibility utilities
- **Pattern:** All I/O operations async, sync wrappers at entry points
- **When:** FastMCP-based servers (always async)

## Standard Directory Structure

```
project-mcp/
├── src/
│   ├── service_mcp/              # MCP server entry point
│   │   ├── __init__.py
│   │   └── server.py             # FastMCP server, tool definitions
│   │
│   └── service_core/              # Reusable libraries
│       ├── __init__.py
│       ├── auth.py               # Authentication/credentials
│       ├── config.py             # Configuration + Pydantic models
│       ├── context.py            # Request context (ID, audit trail)
│       ├── service.py            # Main service class (reusable)
│       ├── cli.py                # CLI commands (cyclopts)
│       ├── logging/              # Logging utilities
│       │   ├── __init__.py
│       │   ├── audit.py          # Audit logging
│       │   └── structured.py     # JSON logging
│       └── utils/                # Utilities
│           ├── __init__.py
│           ├── sanitizer.py      # Credential masking
│           └── retry.py          # Retry with backoff

├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── unit/                     # Fast tests, all mocked
│   │   ├── test_config.py
│   │   ├── test_service.py
│   │   └── test_server.py
│   └── integration/              # Real credentials required
│       └── test_service_integration.py

├── docs/
│   ├── mcp-implementation-guide.md
│   ├── development-guide.md
│   ├── troubleshooting.md
│   └── system-prompts/
│       ├── mcp-standards.md      # This file
│       └── agent-instructions.md # Agentic task descriptions

├── pytest.ini
├── pyproject.toml
├── .env.example
├── README.md
└── CONTRIBUTING.md
```

## Standard Dependencies

### Required
```
FastMCP (from mcp library)
Pydantic >= 2.0
python-dotenv >= 1.0
cyclopts >= 2.0
```

### Development/Testing
```
pytest
pytest-cov
pytest-asyncio
pytest-mock
requests-mock (or equivalent for your service)
```

### Optional Based on Service Type
```
# For Google APIs:
google-api-python-client
google-auth-oauthlib

# For Slack APIs:
slack-sdk

# For AWS APIs:
boto3

# For logging:
python-json-logger
```

## Standard Patterns

### 1. Service Locator Pattern
```python
def get_service(alias_or_profile: str) -> ServiceClass:
    """Get service instance with credentials."""
    config = config_manager.get_resource(alias_or_profile)
    context = RequestContext(profile=config.profile)
    return ServiceClass(context)
```

### 2. Context Object Pattern
```python
class RequestContext:
    def __init__(self, profile: str, request_id: str = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.credentials = auth_manager.get_credentials(profile)

    @property
    def service(self):
        return self.get_service("service_name", "v1")
```

### 3. Structured Tool Response
```python
@mcp.tool()
def tool_name(...) -> dict:
    request_id = set_request_id()
    try:
        result = do_work()
        audit_logger.log_success(...)
        return {"status": "success", "data": result, "request_id": request_id}
    except Exception as e:
        audit_logger.log_error(...)
        return {"status": "error", "message": str(e), "request_id": request_id}
    finally:
        clear_request_id()
```

### 4. Configuration Validation with Pydantic
```python
class ProfileConfig(BaseModel):
    api_token_env: str
    resource_id: Optional[str] = None
    timeout: int = Field(default=30, ge=1, le=300)

class AppConfig(BaseModel):
    profiles: Dict[str, ProfileConfig]

    @validator('profiles')
    def at_least_one_profile(cls, v):
        if not v:
            raise ValueError("At least one profile required")
        return v
```

### 5. CLI Command Pattern
```python
from cyclopts import App

app = App()
config_app = App()

@config_app.command
def list_resources(profile: str = "default"):
    """List available resources."""
    resources = config_manager.list_resources(profile)
    for name, config in resources.items():
        print(f"{name}: {config.description}")

app.command(config_app, name="config")
```

### 6. Test Fixture Pattern
```python
@pytest.fixture
def mock_service():
    """Mock service with predefined responses."""
    service = MagicMock()
    service.do_work.return_value = {"success": True}
    return service

@pytest.fixture
def valid_config():
    """Valid configuration for testing."""
    return AppConfig(
        profiles={
            "default": ProfileConfig(api_token_env="TEST_TOKEN")
        }
    )
```

## Environment Variables Convention

Every MCP project should support these standard environment variables:

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

## Agentic Instruction Guidelines

For agents to effectively use MCP servers:

1. **Tool Descriptions:** Clear, specific, include example usage
2. **Parameter Names:** Use domain-specific terms (sheet_alias, not id)
3. **Return Values:** Structured with status + data + request_id
4. **Error Messages:** Actionable (not just "error", but "Error: Sheet alias 'reports' not found")
5. **Safeguards:** Built-in (resource validation, scope checking)

See `docs/system-prompts/agent-instructions.md` for detailed guidance.

## Sync Protocol

When adopting these standards in a new MCP project:

1. Copy this document to `docs/system-prompts/mcp-standards.md`
2. Update service-specific sections (auth mechanism, APIs, tools)
3. Use standard directory structure as template
4. Copy standard dependencies to pyproject.toml
5. Copy standard patterns to implementation guide
6. Update this document with project-specific deviations

See `docs/mcp-project-sync.md` for detailed sync instructions.
```

### 5.5.3 Project Sync Guide

**File:** `docs/mcp-project-sync.md`

**Purpose:** Document how to sync this documentation and patterns to other MCP projects, maintaining consistency while allowing project-specific customization.

**Content:**

```markdown
# MCP Project Synchronization Guide

This guide explains how to keep documentation and patterns consistent across multiple MCP projects.

## Philosophy

Each MCP project has its own:
- Service layer (Slack, Google Sheets, etc.)
- Authentication mechanism (tokens, OAuth, API keys)
- Specific tools and capabilities

But all MCP projects share:
- Technology stack (FastMCP, Pydantic, cyclopts, pytest)
- Directory structure
- Testing patterns
- Logging patterns
- Configuration patterns
- Documentation structure

## Files to Sync Across Projects

### Always Sync (No Project Changes)
- `docs/system-prompts/mcp-standards.md` - Copy as-is
- `pytest.ini` - Copy as-is
- `.coveragerc` - Copy as-is
- `CONTRIBUTING.md` - Copy as-is (or create symbolic link)

### Sync with Minor Changes
- `docs/mcp-implementation-guide.md` - Copy structure, update service-specific sections
- `docs/development-guide.md` - Copy structure, update setup instructions
- `docs/troubleshooting.md` - Copy structure, add project-specific issues
- `tests/conftest.py` - Copy structure, update service fixtures

### Project-Specific (Don't Sync)
- `docs/system-prompts/agent-instructions.md` - Project's own tools
- `README.md` - Project's own feature set
- All source code files

## Sync Process for New MCP Project

### Step 1: Prepare Template
1. Choose an existing MCP project as template (e.g., google-personal-mcp)
2. Review its `docs/system-prompts/mcp-standards.md`
3. Review its `docs/mcp-implementation-guide.md`

### Step 2: Copy Boilerplate Files
```bash
# Shared documentation (copy as-is)
cp template-project/docs/system-prompts/mcp-standards.md new-project/docs/system-prompts/
cp template-project/pytest.ini new-project/
cp template-project/.coveragerc new-project/
cp template-project/CONTRIBUTING.md new-project/

# Configuration (copy as-is)
cp template-project/pyproject.toml new-project/pyproject.toml
# Then update dependencies for new service type
```

### Step 3: Adapt Implementation Guide
```bash
cp template-project/docs/mcp-implementation-guide.md new-project/docs/

# Then edit to reflect new-project's architecture:
# 1. Service type (Slack vs. Google vs. AWS)
# 2. Authentication mechanism
# 3. API libraries
# 4. Directory structure paths
# 5. Specific tools
# 6. Configuration examples
```

### Step 4: Copy Test Structure
```bash
cp -r template-project/tests/conftest.py new-project/tests/

# Then adapt fixtures for new service:
# 1. Mock objects for new service
# 2. Sample configurations
# 3. Integration test setup
```

### Step 5: Copy Utility Modules
```bash
# Core patterns (copy and adapt)
cp template-project/src/template_core/context.py new-project/src/new_core/
cp template-project/src/template_core/logging/ new-project/src/new_core/
cp template-project/src/template_core/utils/ new-project/src/new_core/

# These are mostly generic and need minimal changes
```

### Step 6: Create Project-Specific Documentation
```bash
# New project's own tool documentation
docs/system-prompts/agent-instructions.md

# Project-specific development notes
docs/development-guide.md (customize the setup section)

# Project-specific troubleshooting
docs/troubleshooting.md (add project-specific issues)
```

## Keeping Projects in Sync

### When Standards Document Changes
If `docs/system-prompts/mcp-standards.md` is updated in one project:

1. Update the source project first
2. Copy updated file to all other MCP projects (no local changes)
3. Each project may add service-specific notes after the standard sections

### When Pattern Emerges in One Project
If a new pattern is discovered in one project (e.g., better retry logic):

1. Document the pattern in that project
2. Add it to `docs/system-prompts/mcp-standards.md`
3. Sync the standard to all projects
4. Each project implements the pattern in its codebase

### Version Tracking
Add to each `docs/system-prompts/mcp-standards.md`:

```
This document is synced across all MCP projects.
Last synced from: google-personal-mcp
Sync date: 2026-01-29
Local adaptations: [List any project-specific changes]
```

## Tools for Sync Management

### Option 1: Git Submodules
```bash
# In each project:
git submodule add https://github.com/user/mcp-standards.git docs/standards
```

Then reference:
```bash
cd docs && ln -s standards/mcp-standards.md mcp-standards.md
```

### Option 2: Git Worktree
```bash
# Maintain a shared standards repo:
git worktree add ../mcp-standards main
cd ../mcp-standards && git pull
# Then copy files from there
```

### Option 3: Manual Sync Script
```bash
#!/bin/bash
# sync-mcp-standards.sh

TEMPLATE_PROJECT=/path/to/google-personal-mcp
PROJECTS=(slack-agent another-mcp project-x)

for project in "${PROJECTS[@]}"; do
  echo "Syncing $project..."
  cp "$TEMPLATE_PROJECT/docs/system-prompts/mcp-standards.md" "$project/docs/system-prompts/"
  cp "$TEMPLATE_PROJECT/pytest.ini" "$project/"
  # ... etc
done
```

## Checklist for New MCP Project

- [ ] Copy mcp-standards.md (no changes)
- [ ] Copy mcp-implementation-guide.md structure and adapt service sections
- [ ] Copy directory structure from template
- [ ] Copy pytest.ini, .coveragerc, CONTRIBUTING.md
- [ ] Update pyproject.toml dependencies for service type
- [ ] Copy conftest.py and adapt service fixtures
- [ ] Copy context.py, logging, utils modules
- [ ] Create project-specific agent-instructions.md
- [ ] Create project-specific development-guide.md
- [ ] Create project-specific troubleshooting.md
- [ ] Update README with project's own tools
- [ ] Verify all imports and file paths correct
- [ ] Run tests: pytest
- [ ] Verify CI/CD integration

## Expected Outcome

After syncing, each MCP project should have:
- ✅ Consistent technology stack
- ✅ Consistent directory structure
- ✅ Consistent testing approach
- ✅ Consistent logging/auditing
- ✅ Consistent configuration pattern
- ✅ Consistent CLI framework
- ✅ Consistent documentation structure
- ✅ Project-specific tools and features

This allows:
- Engineers to move between projects with familiar patterns
- Agents to apply learned strategies to new services
- Patterns to evolve consistently across ecosystem
- Code to be reusable (core utilities work everywhere)
```

### 5.5.4 Agentic Instruction Framework

**File:** `docs/system-prompts/agent-instructions.md`

**Purpose:** Define how slack-agent tools should be described to agents (Claude, other LLMs) for maximum effectiveness.

**Content Structure:**

1. **Tool Catalog** - List of all MCP tools with:
   - Clear, specific descriptions
   - Expected parameters
   - Example usage
   - Common error modes and recovery

2. **Domain Context** - Information agents need to know:
   - Slack's data model (workspaces, channels, users, messages)
   - Bot capabilities and limitations
   - Rate limits and best practices
   - Permission requirements

3. **Usage Patterns** - How agents should compose tools:
   - Listing resources first
   - Error recovery strategies
   - Batching patterns
   - Thread management

4. **Error Handling Guide** - How to respond to tool failures:
   - Token errors → re-authentication needed
   - Permission errors → check bot permissions
   - Channel errors → list available channels
   - Rate limit errors → exponential backoff

---

**Files Count Update:**

The documentation enhancements add:

**New Files:**
- `docs/mcp-implementation-guide.md` (slack-agent specific, ~3000 lines)
- `docs/system-prompts/mcp-standards.md` (shared standards, ~1200 lines)
- `docs/mcp-project-sync.md` (sync procedures, ~500 lines)
- `docs/system-prompts/agent-instructions.md` (slack-agent tools, ~800 lines)

Total documentation lines: +5500

## Phase 6: Advanced Features (Optional)

### 6.1 Retry Logic with Exponential Backoff

**Goal:** Automatic retry for transient Slack API failures.

**Files to Create:**
- `src/slack_notifications/utils/retry.py` - Retry decorator

**Implementation:**
```python
@retry_on_rate_limit(max_retries=3, backoff_base=2)
def send_message(...):
    # Retries on HTTP 429, 500, 502, 503, 504
    # Backoff: 2s, 4s, 8s
```

### 6.2 Batch Message Support

**Goal:** Send multiple messages in a single tool call.

**Files to Modify:**
- `src/slack_notifications/mcp_server.py` - Add `send_batch_messages` tool

### 6.3 Thread Support

**Goal:** Reply to message threads.

**Files to Modify:**
- `src/slack_notifications/notifier.py` - Add thread_ts parameter
- `src/slack_notifications/mcp_server.py` - Add thread support to tools

## Implementation Order

1. **Phase 1** (Core Infrastructure) - Foundation for all other work
2. **Phase 2** (Configuration) - Enables profile support and better error messages
3. **Phase 4** (Testing) - Validate Phase 1 & 2 before continuing
4. **Phase 3** (CLI) - Requires working config and testing
5. **Phase 5 & 5.5** (Documentation) - Document completed features + standardize for portability
   - Phase 5: Project-specific guides
   - Phase 5.5: Portable standards for multi-project sync
6. **Phase 6** (Advanced) - Optional enhancements

**Rationale:**
- Core infrastructure first because all other features depend on it
- Configuration before CLI because CLI needs configuration system
- Testing early to validate foundation before building on it
- Documentation together (both phases) at the end to reflect actual implementation
- **Phase 5.5 is critical:** Creates portable documentation that can be synced to other MCP projects, establishing consistency across the MCP ecosystem

## Files to Create/Modify

### New Files (27 files)
- `src/slack_notifications/utils/__init__.py`
- `src/slack_notifications/utils/context.py`
- `src/slack_notifications/utils/sanitizer.py`
- `src/slack_notifications/utils/retry.py`
- `src/slack_notifications/logging/__init__.py`
- `src/slack_notifications/logging/audit.py`
- `src/slack_notifications/logging/structured.py`
- `src/slack_notifications/cli.py`
- `tests/conftest.py`
- `tests/unit/__init__.py`
- `tests/unit/test_config.py`
- `tests/unit/test_notifier.py`
- `tests/unit/test_mcp_server.py`
- `tests/unit/test_utils.py`
- `tests/integration/__init__.py`
- `tests/integration/test_slack_integration.py`
- `docs/development-guide.md`
- `docs/troubleshooting.md`
- `docs/implementation-reference.md`
- `docs/mcp-implementation-guide.md` - **Slack-specific implementation patterns**
- `docs/mcp-project-sync.md` - **How to sync to other MCP projects**
- `docs/system-prompts/mcp-standards.md` - **Shared MCP technology standards** (portable)
- `docs/system-prompts/agent-instructions.md` - **Slack-agent tool descriptions for agents**
- `pytest.ini`
- `~/.config/slack-agent/config.json` (user config)
- `.coveragerc`
- `CONTRIBUTING.md`

### Modified Files (8 files)
- `src/slack_notifications/config.py` - Profile support, Pydantic models
- `src/slack_notifications/mcp_server.py` - Request IDs, audit logging, structured responses
- `src/slack_notifications/notifier.py` - Profile support, retry logic
- `src/slack_notifications/client.py` - Request ID propagation
- `pyproject.toml` - New dependencies (cyclopts, python-dotenv, pydantic), CLI entry point
- `requirements.txt` - Sync with pyproject.toml
- `.env.example` - Profile-based environment variables
- `README.md` - CLI documentation, profile examples

### Not Modified
- `src/slack_notifications/exceptions.py` - Already well-designed
- `src/slack_agent/__main__.py` - Out of scope (separate agent)
- `tests/test_*.py` (existing) - Will be replaced by new test structure

## Success Criteria

✅ Request ID tracking in all MCP tool responses
✅ Audit log written to `~/.config/slack-agent/audit.log`
✅ Credentials masked in all logs (unless `SLACK_AGENT_DEBUG=1`)
✅ Profile-based configuration working
✅ Pydantic validation catching invalid config
✅ CLI commands functional: `slack-agent config|test|debug`
✅ Unit tests pass with >85% coverage
✅ Integration tests pass (with credentials)
✅ Documentation complete (development, troubleshooting, implementation)
✅ All changes verified and documented in dev_notes/changes/

## Risk Assessment

### Low Risk
- Utility modules (context, sanitizer) - Self-contained, easy to test
- Documentation - No code changes
- CLI - Optional feature, doesn't affect MCP server

### Medium Risk
- Configuration refactoring - Could break existing deployments
  - **Mitigation:** Maintain backward compatibility with environment variables
  - **Mitigation:** Add migration guide in documentation
- Pydantic validation - Could reject previously valid configs
  - **Mitigation:** Comprehensive validation tests
  - **Mitigation:** Clear error messages

### High Risk
- MCP server refactoring - Changes core functionality
  - **Mitigation:** Extensive unit and integration tests
  - **Mitigation:** Maintain existing tool signatures
  - **Mitigation:** Phase implementation (test each tool individually)
- Profile system - New concept for users
  - **Mitigation:** Default profile works like current behavior
  - **Mitigation:** Clear migration documentation

## Estimated Scope

- **New code:** ~2000 lines
  - Utils: ~200 lines
  - Logging: ~300 lines
  - CLI: ~500 lines
  - Tests: ~1000 lines

- **Modified code:** ~500 lines
  - MCP server refactor: ~200 lines
  - Config refactor: ~200 lines
  - Other: ~100 lines

- **Documentation:** ~8500 lines
  - **Project-Specific Guides** (~4000 lines):
    - Development guide: ~500 lines
    - Troubleshooting guide: ~800 lines
    - Implementation reference: ~1200 lines
    - MCP implementation guide (slack-agent specific): ~1000 lines
  - **Portable Standards** (~3000 lines):
    - MCP standards document (sharable across projects): ~1200 lines
    - MCP project sync guide: ~500 lines
    - Agent instructions framework: ~800 lines
  - **Other documentation** (~500 lines):
    - README updates: ~200 lines
    - CONTRIBUTING: ~300 lines

- **Configuration files:** ~300 lines
  - pytest.ini, .coveragerc, config.json examples

**Key Documentation Advantage:**
- `docs/system-prompts/mcp-standards.md` (~1200 lines) is a **single source of truth** that can be manually synced to all MCP projects (slack-agent, google-personal-mcp, etc.)
- `docs/mcp-project-sync.md` provides clear instructions for maintaining consistency across projects
- Project-specific guides reference the standards, reducing duplication

## Dependencies to Add

**Core:**
- `pydantic>=2.0` - Configuration validation
- `python-dotenv>=1.0` - .env file support
- `cyclopts>=2.0` - CLI framework

**Development:**
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `requests-mock` - HTTP mocking for Slack API

## Migration Guide

For existing users:

1. **No immediate action required** - Environment variables still work
2. **Optional:** Create `~/.config/slack-agent/config.json` for multi-profile support
3. **Optional:** Use new CLI for testing: `slack-agent test send-message "test"`
4. **Recommended:** Review audit log location and size management

**Breaking Changes:**
- None - All changes are backward compatible

**Deprecations:**
- None planned

## Known Limitations

- Profile system requires manual config.json creation (no auto-migration from env vars)
- Audit log has no built-in rotation (user responsible for cleanup)
- CLI commands require separate installation step
- Integration tests require real Slack workspace

## Next Steps After Approval

1. Create Phase 1 implementation in single commit
2. Verify audit logging and request IDs working
3. Create Phase 2 configuration changes
4. Add comprehensive test suite
5. Implement CLI commands
6. Write documentation
7. Update dev_notes/changes/ with verification

## Checklist for Completion

- [ ] Phase 1: Core Infrastructure Implemented
- [ ] Phase 2: Configuration Enhancements Implemented
- [ ] Phase 3: CLI Tools Implemented
- [ ] Phase 4: Testing Infrastructure Implemented
- [ ] Phase 5: Project-Specific Documentation Completed
- [ ] Phase 5.5: Portable MCP Standards Documentation Completed
  - [ ] `docs/mcp-implementation-guide.md` (slack-agent patterns)
  - [ ] `docs/system-prompts/mcp-standards.md` (sharable across projects)
  - [ ] `docs/mcp-project-sync.md` (sync procedures)
  - [ ] `docs/system-prompts/agent-instructions.md` (agent toolkit)
- [ ] All tests passing (unit + integration)
- [ ] Coverage targets met (>85%)
- [ ] Documentation reviewed and complete
- [ ] Standards documentation verified for portability (can be synced to other projects)
- [ ] Change log created in dev_notes/changes/
- [ ] Status updated to "Completed"

---

**Note:** This plan deliberately excludes TUI box graphics mentioned in the inbox spec, focusing instead on battle-tested patterns from google-personal-mcp that improve maintainability, debuggability, and user experience.

**Documentation Standards (Phase 5.5):** Includes comprehensive, portable documentation standards designed for manual syncing across multiple MCP projects. The `docs/system-prompts/mcp-standards.md` document serves as a single source of truth for MCP technology choices and patterns, enabling agentic systems to apply learned strategies consistently across the entire MCP ecosystem (slack-agent, google-personal-mcp, and future projects).
