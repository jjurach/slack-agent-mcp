# Implementation Reference

This document provides practical implementation patterns and reference implementations for the Google Personal MCP Server. It consolidates patterns for MCP tool development, Google API integration, configuration management, testing, and CLI commands.

## Quick Reference

- **Adding a new MCP tool**: See [MCP Tool Development](#mcp-tool-development-pattern)
- **Integrating a new Google API**: See [Google API Integration](#google-api-integration-pattern)
- **Adding a CLI command**: See [CLI Command Pattern](#cli-command-pattern)
- **Writing tests**: See [Testing Patterns](#testing-patterns)
- **Configuration management**: See [Configuration Patterns](#configuration-patterns)

## MCP Tool Development Pattern

### Standard Tool Template

All MCP tools follow this standard pattern:

```python
from fastmcp import FastMCP
from google_mcp_core.utils.context import set_request_id, get_request_id, clear_request_id
from google_mcp_core.utils.sanitizer import mask_credentials, should_sanitize
from google_mcp_core.logging.audit import get_audit_logger

audit_logger = get_audit_logger()

@mcp.tool()
def tool_name(param1: str, param2: int, optional_param: str = "default") -> dict:
    """
    Brief description of what this tool does.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        optional_param: Description of optional parameter

    Returns:
        dict: Response with status, data/message, and request_id
    """
    request_id = set_request_id()
    try:
        # 1. Get appropriate service instance
        service, resource_id = get_sheets_service(param1)  # or get_drive_service()

        # 2. Perform the operation
        result = service.operation_method(resource_id, param2)

        # 3. Log success to audit trail
        audit_logger.log_tool_call(
            tool_name="tool_name",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=True
        )

        # 4. Return success response
        return {
            "status": "success",
            "result": result,
            "request_id": request_id
        }

    except Exception as e:
        # 5. Mask credentials in error messages
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)

        # 6. Log error to audit trail
        audit_logger.log_tool_call(
            tool_name="tool_name",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=False,
            error_message=error_msg
        )

        # 7. Return error response
        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id
        }

    finally:
        # 8. Always clear request context
        clear_request_id()
```

### Key Implementation Details

**Request ID Management:**
- Call `set_request_id()` at the start of every tool
- Include `request_id` in all responses
- Call `clear_request_id()` in `finally` block

**Error Handling:**
- Always catch `Exception` (broad catch for MCP tools)
- Mask credentials using `mask_credentials()` when not in debug mode
- Return structured error response (never raise exceptions to MCP)

**Audit Logging:**
- Log tool call parameters (sanitized)
- Log success/failure status
- Include request_id for tracing

**Response Format:**
- Always return `dict` with `status` field
- Include `request_id` for tracing
- Use `result` for success data, `message` for errors

## Google API Integration Pattern

### Adding a New Service

When integrating a new Google API (e.g., Gmail, Calendar):

**Step 1: Add OAuth scopes** in `src/google_mcp_core/auth.py`:

```python
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",  # NEW SCOPE
]
```

**Step 2: Create service class** in `src/google_mcp_core/gmail.py`:

```python
from typing import List, Dict, Any
from google_mcp_core.context import GoogleContext

class GmailService:
    """Wrapper for Gmail API operations."""

    def __init__(self, context: GoogleContext):
        """Initialize service with GoogleContext."""
        self.context = context
        self.service = context.get_service("gmail", "v1")

    def list_messages(self, query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
        """List messages matching query."""
        results = self.service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        return results.get("messages", [])

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get full message by ID."""
        return self.service.users().messages().get(
            userId="me",
            id=message_id
        ).execute()
```

**Step 3: Add service locator** in `src/google_personal_mcp/server.py`:

```python
def get_gmail_service(profile: str = "default") -> GmailService:
    """Get GmailService instance for profile."""
    context = GoogleContext(profile=profile)
    return GmailService(context)
```

**Step 4: Add MCP tools** using the standard tool template above.

**Step 5: Force re-authentication** (new scopes require user consent):

```bash
rm ~/.config/google-personal-mcp/profiles/*/token.json
```

Users will be prompted to re-authenticate on next use.

### Service Design Principles

**GoogleContext Pattern:**
- Each service receives a `GoogleContext` instance
- Context handles credential management and caching
- Services never directly manage credentials

**Lazy Service Creation:**
- Services created only when needed via `context.get_service()`
- Service instances cached per context
- Reduces startup time and memory usage

**Minimal Business Logic:**
- Services are thin wrappers around Google APIs
- Return raw or lightly processed API responses
- Business logic belongs in tool layer

**API Version Pinning:**
- Always specify API version in `get_service()` call
- Example: `get_service("sheets", "v4")` not `get_service("sheets", "latest")`
- Prevents breaking changes from API updates

## Configuration Patterns

### Resource Alias System

Resource aliases allow tools to reference resources by name instead of ID:

```python
# In config.json
{
  "sheets": {
    "prompts": {
      "id": "1ABC123XYZ...",
      "profile": "default",
      "description": "Main prompts storage"
    },
    "work-notes": {
      "id": "1DEF456UVW...",
      "profile": "work",
      "description": "Work-related notes"
    }
  }
}

# In tool code
service, spreadsheet_id = get_sheets_service("prompts")
# Automatically resolves: alias → config → ID + profile → service
```

### Adding New Resource Types

**Step 1: Define model** in `src/google_mcp_core/config.py`:

```python
from pydantic import BaseModel

class CalendarResourceConfig(BaseModel):
    """Configuration for a calendar resource."""
    id: str
    profile: str = "default"
    description: str = ""

class AppConfig(BaseModel):
    """Application configuration."""
    sheets: Dict[str, SheetResourceConfig] = {}
    drive: DriveConfig = DriveConfig()
    calendars: Dict[str, CalendarResourceConfig] = {}  # NEW
```

**Step 2: Add accessor methods**:

```python
class ConfigManager:
    def get_calendar_resource(self, alias: str) -> CalendarResourceConfig:
        """Get calendar resource by alias."""
        config = self.get_config()
        if alias not in config.calendars:
            raise ValueError(f"Calendar alias '{alias}' not found in config")
        return config.calendars[alias]
```

**Step 3: Add service locator**:

```python
def get_calendar_service(alias: str) -> Tuple[CalendarService, str]:
    """Get CalendarService and calendar ID from alias."""
    resource = config_manager.get_calendar_resource(alias)
    context = GoogleContext(profile=resource.profile)
    return CalendarService(context), resource.id
```

### Environment-Based Configuration

Support multiple environments (dev, staging, prod):

```bash
# Development
export GOOGLE_MCP_ENV=dev
export GOOGLE_PERSONAL_MCP_CONFIG=/path/to/config.dev.json

# Staging
export GOOGLE_MCP_ENV=staging
export GOOGLE_PERSONAL_MCP_CONFIG=/path/to/config.staging.json

# Production (uses default ~/.config location)
unset GOOGLE_MCP_ENV
unset GOOGLE_PERSONAL_MCP_CONFIG
```

## Testing Patterns

### Google API Mocking with Pytest Fixtures

**Core fixture pattern** in `tests/conftest.py`:

```python
import pytest
from unittest.mock import MagicMock, Mock
from google_mcp_core.context import GoogleContext
from google_mcp_core.sheets import SheetsService

@pytest.fixture
def mock_google_context():
    """Mock GoogleContext to avoid real API calls."""
    mock_ctx = MagicMock(spec=GoogleContext)
    mock_ctx.profile = "default"

    # Mock credentials
    mock_creds = Mock()
    mock_creds.valid = True
    mock_ctx.credentials = mock_creds

    # Mock get_service() to return mock service
    mock_service = MagicMock()
    mock_ctx.get_service = Mock(return_value=mock_service)

    return mock_ctx

@pytest.fixture
def mock_sheets_service(mock_google_context):
    """Create SheetsService with mocked context."""
    service = SheetsService(mock_google_context)

    # Configure common mock responses
    mock_response = {
        "sheets": [
            {"properties": {"title": "Sheet1"}},
            {"properties": {"title": "Sheet2"}}
        ]
    }

    service.service.spreadsheets().get().execute.return_value = mock_response

    return service
```

### Unit Test Pattern

```python
def test_list_sheet_titles(mock_sheets_service):
    """Test listing sheet titles."""
    # Arrange - setup mock response
    mock_sheets_service.service.spreadsheets().get().execute.return_value = {
        "sheets": [
            {"properties": {"title": "Sheet1"}},
            {"properties": {"title": "Sheet2"}}
        ]
    }

    # Act - call service method
    titles = mock_sheets_service.list_sheet_titles("fake_sheet_id")

    # Assert - verify result
    assert titles == ["Sheet1", "Sheet2"]

    # Verify API was called correctly
    mock_sheets_service.service.spreadsheets().get.assert_called_once()
```

### Integration Test Pattern

```python
@pytest.mark.integration
@pytest.mark.skipif(not has_credentials(), reason="Requires credentials")
def test_list_sheets_integration():
    """Integration test with real Google API."""
    # Use real context and credentials
    context = GoogleContext(profile="default")
    service = SheetsService(context)

    # Use real spreadsheet ID from environment
    sheet_id = os.getenv("TEST_SPREADSHEET_ID")
    if not sheet_id:
        pytest.skip("TEST_SPREADSHEET_ID not set")

    # Call real API
    titles = service.list_sheet_titles(sheet_id)

    # Verify real response
    assert isinstance(titles, list)
    assert len(titles) > 0
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_sheets_service.py
│   ├── test_drive_service.py
│   └── test_config.py
├── integration/
│   ├── test_sheets_integration.py
│   └── test_drive_integration.py
└── e2e/
    └── test_mcp_tools.py    # End-to-end MCP tool tests
```

**Run specific test suites:**

```bash
# Unit tests only (fast, no API calls)
pytest tests/unit/ -v

# Integration tests (requires credentials)
pytest tests/integration/ -v -m integration

# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/google_mcp_core --cov-report=term-missing
```

### Credential Masking Tests

```python
from google_mcp_core.utils.sanitizer import mask_credentials

def test_oauth_token_masking():
    """Test that OAuth tokens are masked."""
    error = "Error: Token ya29.a0AfH6SMBx... expired"
    masked = mask_credentials(error)

    assert "ya29" not in masked
    assert "***REDACTED:OAUTH_TOKEN***" in masked

def test_api_key_masking():
    """Test that API keys are masked."""
    error = "Invalid API key: AIzaSyD..."
    masked = mask_credentials(error)

    assert "AIzaSy" not in masked
    assert "***REDACTED:API_KEY***" in masked
```

## CLI Command Pattern

### Adding a New CLI Command

The CLI uses a configuration-driven approach. To add a command:

**Step 1: Define command handler** in `src/google_mcp_core/cli.py`:

```python
def cmd_sheets_create_tab(args):
    """Create a new sheet tab."""
    try:
        # Get service
        service, spreadsheet_id = get_sheets_service(args.alias)

        # Perform operation
        result = service.create_sheet(spreadsheet_id, args.title)

        # Output result
        print(f"Created tab: {args.title}")
        print(f"Sheet ID: {result['replies'][0]['addSheet']['properties']['sheetId']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

**Step 2: Register in COMMANDS dictionary**:

```python
COMMANDS = {
    "sheets": {
        "list-tabs": {
            "handler": cmd_sheets_list_tabs,
            "help": "List all tabs in a sheet",
            "args": [
                {"name": "alias", "help": "Sheet alias"}
            ]
        },
        "create-tab": {  # NEW COMMAND
            "handler": cmd_sheets_create_tab,
            "help": "Create a new tab in a sheet",
            "args": [
                {"name": "alias", "help": "Sheet alias"},
                {"name": "title", "help": "Tab title"}
            ]
        }
    },
    # ... other command groups
}
```

**Step 3: Test the command**:

```bash
google-personal-mcp sheets create-tab prompts "New Sheet"
```

### CLI Design Principles

**Reuse Service Layer:**
- CLI commands call the same service methods as MCP tools
- No duplicate business logic
- Consistent behavior across interfaces

**Configuration-Driven:**
- Commands defined in `COMMANDS` dictionary
- Parser built automatically from configuration
- Minimal boilerplate for new commands

**User-Friendly Output:**
- Use `print()` for normal output
- Use `print(..., file=sys.stderr)` for errors
- Use exit codes (0=success, 1=error)

**Help Text:**
- Command help text auto-generated from config
- Use docstrings for handler functions
- Provide clear argument descriptions

## Error Handling Patterns

### Retry Logic

Use `@retry_on_rate_limit` decorator for API operations:

```python
from google_mcp_core.utils.retry import retry_on_rate_limit

class SheetsService:
    @retry_on_rate_limit(max_retries=3, backoff_base=2)
    def get_values(self, spreadsheet_id: str, range_name: str):
        """Get cell values with automatic retry on rate limit."""
        return self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
```

**Retry behavior:**
- Retries on HTTP 429 (rate limit) and 5xx errors
- Exponential backoff: 2s, 4s, 8s
- Configurable max retries
- Logs retry attempts

### Access Control

Enforce access restrictions in service layer:

```python
class DriveService:
    def __init__(self, context: GoogleContext):
        self.service = context.get_service("drive", "v3")
        config = config_manager.get_config()
        self.allowed_folder_ids = config.drive.folder_ids

    def _verify_access(self, parent_id: str):
        """Verify parent folder is in allowed list."""
        if parent_id not in self.allowed_folder_ids:
            raise AccessDeniedError(
                f"Access denied: folder {parent_id} not in allowed list. "
                f"Configure allowed folders in config.json"
            )

    def create_file(self, name: str, parent_id: str, mime_type: str):
        """Create file with access verification."""
        self._verify_access(parent_id)  # Check before API call

        file_metadata = {
            "name": name,
            "parents": [parent_id],
            "mimeType": mime_type
        }

        return self.service.files().create(
            body=file_metadata,
            fields="id,name,mimeType,createdTime"
        ).execute()
```

### Custom Exceptions

Define domain-specific exceptions in `src/google_mcp_core/exceptions.py`:

```python
class GoogleMCPError(Exception):
    """Base exception for Google MCP errors."""
    pass

class AuthenticationError(GoogleMCPError):
    """Raised when authentication fails."""
    pass

class AccessDeniedError(GoogleMCPError):
    """Raised when access to a resource is denied."""
    pass

class ResourceNotFoundError(GoogleMCPError):
    """Raised when a configured resource is not found."""
    pass

class InvalidConfigurationError(GoogleMCPError):
    """Raised when configuration is invalid."""
    pass
```

**Usage in tools:**

```python
try:
    service, sheet_id = get_sheets_service(alias)
except ResourceNotFoundError as e:
    return {
        "status": "error",
        "message": f"Sheet alias '{alias}' not found in configuration",
        "request_id": request_id
    }
```

## Logging Patterns

### Structured Logging

Use structured logging for machine-parseable logs:

```python
from google_mcp_core.logging.structured import get_logger

logger = get_logger(__name__)

# Log with structured context
logger.info("Operation completed", extra={
    "request_id": request_id,
    "spreadsheet_id": sheet_id,
    "range": range_name,
    "rows_read": len(values),
    "duration_ms": elapsed_time
})
```

**Enable JSON logging:**

```bash
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
```

**Output format:**

```json
{
  "timestamp": "2026-01-27T12:34:56.789Z",
  "level": "INFO",
  "logger": "google_mcp_core.sheets",
  "message": "Operation completed",
  "request_id": "abc-123-def",
  "spreadsheet_id": "1ABC...",
  "range": "Sheet1!A1:B10",
  "rows_read": 42,
  "duration_ms": 234
}
```

### Audit Logging

All tool calls automatically logged to audit trail:

```python
from google_mcp_core.logging.audit import get_audit_logger

audit_logger = get_audit_logger()

audit_logger.log_tool_call(
    tool_name="read_cells",
    parameters={"sheet_alias": "prompts", "range": "A1:B10"},
    request_id=request_id,
    success=True,
    result_summary={"rows": 42}  # Optional
)
```

**View audit log:**

```bash
# Real-time monitoring
tail -f ~/.config/google-personal-mcp/audit.log | jq .

# Filter by tool
cat ~/.config/google-personal-mcp/audit.log | jq 'select(.tool_name=="read_cells")'

# Filter by errors
cat ~/.config/google-personal-mcp/audit.log | jq 'select(.success==false)'

# Filter by time range
cat ~/.config/google-personal-mcp/audit.log | jq 'select(.timestamp >= "2026-01-27T10:00:00")'
```

## Performance Patterns

### Service Caching

`GoogleContext` automatically caches service instances:

```python
# First call - creates service (~100-200ms)
sheets_service = context.get_service("sheets", "v4")

# Subsequent calls - returns cached instance (~1ms)
sheets_service = context.get_service("sheets", "v4")
```

**Best practice:** Reuse `GoogleContext` instances when possible.

### Batch Operations

Use batch APIs when performing multiple operations:

```python
# Bad: Multiple round trips
for row in rows:
    service.append_row(sheet_id, range_name, row)

# Good: Single batch request
batch_data = [{"range": f"Sheet1!A{i}", "values": [[row]]} for i, row in enumerate(rows, 1)]
service.batch_update_values(sheet_id, batch_data)
```

### Lazy Loading

Only load resources when needed:

```python
class GoogleContext:
    @property
    def credentials(self):
        """Lazy-load credentials on first access."""
        if not self._creds:
            self._creds = self.auth_manager.get_credentials(profile=self.profile)
        return self._creds
```

## See Also

- [Architecture](architecture.md) - System design and architecture
- [Development Guide](development.md) - Detailed development practices
- [AGENTS.md](../AGENTS.md) - Core workflow for AI agents
- [Definition of Done](definition-of-done.md) - Quality standards

---
Last Updated: 2026-01-27
