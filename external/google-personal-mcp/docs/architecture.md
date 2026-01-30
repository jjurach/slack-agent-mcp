# System Architecture

This document describes the architecture of the Google Personal MCP Server, including the MCP server layer, Google API integration, authentication patterns, and CLI tool architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastMCP Server                          │
│        (Handles MCP protocol & tool registration)           │
├─────────────────────────────────────────────────────────────┤
│                      Tool Layer                             │
│    (Tool definitions, parameter validation, error handling) │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                            │
│  (SheetsService, DriveService, ConfigManager, GoogleContext)│
├─────────────────────────────────────────────────────────────┤
│                  Authentication Layer                       │
│         (AuthManager, credential handling, profiles)        │
├─────────────────────────────────────────────────────────────┤
│                  Google APIs (Sheets v4, Drive v3)          │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── google_personal_mcp/
│   ├── __init__.py
│   └── server.py                  # MCP server entry point, tools
│
└── google_mcp_core/
    ├── __init__.py
    ├── auth.py                    # OAuth2 authentication
    ├── config.py                  # Configuration management
    ├── context.py                 # GoogleContext (service facade)
    ├── sheets.py                  # Sheets API wrapper
    ├── drive.py                   # Drive API wrapper
    ├── cli.py                     # CLI commands
    ├── exceptions.py              # Custom exceptions
    ├── utils/
    │   ├── retry.py               # Retry decorator
    │   ├── sanitizer.py           # Credential masking
    │   └── context.py             # Request ID context
    ├── logging/
    │   ├── structured.py          # JSON logging
    │   └── audit.py               # Audit logging
    └── scripts/
        └── drive_tool.py          # Diagnostic script
```

## MCP Server Architecture

### Tool Layer

The tool layer is implemented in `src/google_personal_mcp/server.py` and provides MCP tool definitions that wrap service layer operations.

**Key Responsibilities:**
- Define tool signatures and parameter schemas
- Validate input parameters
- Handle errors and return structured responses
- Integrate with audit logging
- Mask credentials in error messages

**Standard Tool Pattern:**

```python
@mcp.tool()
def tool_name(param1: str, param2: int) -> dict:
    """Tool description."""
    request_id = set_request_id()
    try:
        # Get appropriate service
        service, resource_id = get_service(param1)

        # Perform operation
        result = service.operation(resource_id, param2)

        # Log success
        audit_logger.log_tool_call(
            tool_name="tool_name",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=True
        )

        return {
            "status": "success",
            "result": result,
            "request_id": request_id
        }
    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)

        audit_logger.log_tool_call(
            tool_name="tool_name",
            parameters={"param1": param1, "param2": param2},
            request_id=request_id,
            success=False,
            error_message=error_msg
        )

        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id
        }
    finally:
        clear_request_id()
```

### Service Locator Pattern

Services are instantiated through service locator functions that handle configuration lookup and profile resolution:

```python
def get_sheets_service(alias: str) -> Tuple[SheetsService, str]:
    """Get SheetsService instance and resource ID from alias."""
    resource = config_manager.get_sheet_resource(alias)
    context = GoogleContext(profile=resource.profile)
    return SheetsService(context), resource.id

def get_drive_service(profile: str = "default") -> DriveService:
    """Get DriveService instance for profile."""
    context = GoogleContext(profile=profile)
    return DriveService(context)
```

**Benefits:**
- Centralizes service instantiation logic
- Handles configuration lookup transparently
- Simplifies tool implementation
- Enables consistent error handling

## Service Layer

### GoogleContext (Service Facade)

`GoogleContext` is the central facade for Google API access. It provides:

- **Lazy credential loading** - Credentials loaded only when needed
- **Service caching** - API service instances cached per context
- **Profile management** - Isolates authentication per profile

```python
class GoogleContext:
    """Lazy-loads credentials and caches service instances."""

    def __init__(self, profile: str = "default"):
        self.profile = profile
        self.auth_manager = AuthManager()
        self._creds = None
        self._services = {}

    @property
    def credentials(self):
        """Lazy-load credentials on first access."""
        if not self._creds:
            self._creds = self.auth_manager.get_credentials(profile=self.profile)
        return self._creds

    def get_service(self, service_name: str, version: str):
        """Get or create cached API service."""
        key = f"{service_name}:{version}"
        if key not in self._services:
            self._services[key] = build(
                service_name, version, credentials=self.credentials
            )
        return self._services[key]
```

### SheetsService

Wraps Google Sheets API v4 operations:

- List sheet tabs
- Read cell ranges
- Update cell ranges
- Append rows
- Batch operations

**Design Principles:**
- One method per API operation
- Returns raw API responses
- No business logic
- Minimal error handling (let tool layer handle)

### DriveService

Wraps Google Drive API v3 operations with access control:

- Create files and folders
- List files with filtering
- Search files
- Update file metadata
- Enforce folder access restrictions

**Access Control Pattern:**

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
                f"Access denied: {parent_id} not in allowed folders"
            )

    def create_file(self, name: str, parent_id: str, ...):
        """Create file with access verification."""
        self._verify_access(parent_id)
        # ... create file
```

All Drive operations validate against configured folder list before execution.

## Authentication Layer

### Profile-Based Credential Storage

Credentials are organized by profile to support multiple Google accounts:

```
~/.config/google-personal-mcp/
├── config.json              # Resource aliases and configuration
└── profiles/
    ├── default/
    │   ├── credentials.json  # OAuth 2.0 client secrets
    │   └── token.json        # Authorization token (auto-generated)
    └── work/                 # Alternative profile example
        ├── credentials.json
        └── token.json
```

### OAuth2 Flow

1. **Initial Authentication:**
   - Check for `credentials.json` in profile directory
   - If no `token.json` or invalid, initiate OAuth2 flow
   - Open browser for user consent
   - Exchange authorization code for access/refresh tokens
   - Save tokens to `token.json`

2. **Subsequent Requests:**
   - Load tokens from `token.json`
   - Check token expiration
   - Refresh if needed
   - Use access token for API calls

3. **Token Refresh:**
   - Automatic when token expired
   - Uses refresh token from `token.json`
   - Updates `token.json` with new access token

### AuthManager

`AuthManager` handles all authentication operations:

```python
class AuthManager:
    def get_credentials(self, profile: str = "default") -> Credentials:
        """Get credentials for profile, refreshing if needed."""
        token_path = self._get_token_path(profile)
        creds_path = self._get_credentials_path(profile)

        # Load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path))
            if creds.valid:
                return creds
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_token(creds, token_path)
                return creds

        # New authentication flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(creds_path), scopes=SCOPES
        )
        creds = flow.run_local_server(port=0)
        self._save_token(creds, token_path)
        return creds
```

### OAuth Scopes

Current scopes required:

```python
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
```

Adding new scopes requires:
1. Update `SCOPES` in `auth.py`
2. Delete existing `token.json` files (forces re-authentication)
3. Create corresponding service class
4. Add CLI diagnostic commands
5. Document in README

## Configuration Management

### ConfigManager

`ConfigManager` handles:

- Loading/saving `config.json`
- Managing resource aliases (sheets, drives)
- Drive folder access control lists
- Profile associations

### Configuration Schema

```json
{
  "sheets": [
    {
      "alias": "prompts",
      "id": "1ABC...",
      "profile": "default"
    }
  ],
  "drive": {
    "folder_ids": [
      "1XYZ..."
    ]
  }
}
```

### Resource Aliases

Resource aliases allow tools to reference resources by name instead of ID:

```python
# Instead of:
result = read_cells(spreadsheet_id="1ABC123...", range="Sheet1!A1:B10")

# Use:
result = read_cells(sheet_alias="prompts", range="Sheet1!A1:B10")
```

## CLI Tool Architecture

### Command Structure

The CLI is implemented using Python's `argparse` and provides diagnostic and management commands:

```bash
google-personal-mcp <command> [options]
```

### Available Commands

**Authentication:**
- `auth login [--profile=<name>]` - Authenticate profile
- `auth status [--profile=<name>]` - Check authentication status

**Sheets:**
- `sheets list-tabs <alias>` - List sheet tabs
- `sheets read <alias> <range>` - Read cell range

**Drive:**
- `drive list [--folder-id=<id>]` - List files
- `drive search <query>` - Search files

**Configuration:**
- `config show` - Display current configuration
- `config add-sheet <alias> <id> [--profile=<name>]` - Add sheet alias

### CLI Architecture

The CLI tool is implemented in `src/google_mcp_core/cli.py` and follows a configuration-driven design:

```python
COMMANDS = {
    "auth": {
        "login": {"handler": cmd_auth_login, "args": [...]},
        "status": {"handler": cmd_auth_status, "args": [...]},
    },
    "sheets": {
        "list-tabs": {"handler": cmd_sheets_list_tabs, "args": [...]},
        "read": {"handler": cmd_sheets_read, "args": [...]},
    },
    # ...
}

def main():
    parser = build_parser_from_config(COMMANDS)
    args = parser.parse_args()
    command_handler = resolve_handler(args)
    command_handler(args)
```

**Design Principles:**
- Configuration-driven command registration
- Minimal boilerplate for adding commands
- Consistent argument parsing
- Reuses service layer (no duplication)

## Error Handling Patterns

### Credential Masking

All errors are sanitized to prevent credential leakage:

```python
from google_mcp_core.utils.sanitizer import mask_credentials, should_sanitize

try:
    result = api_call()
except Exception as e:
    error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)
    return {"status": "error", "message": error_msg}
```

**Patterns Masked:**
- OAuth tokens (ya29.*, 1//*) → `***REDACTED:OAUTH_TOKEN***`
- API keys → `***REDACTED:API_KEY***`
- Bearer tokens → `***REDACTED:BEARER_TOKEN***`

**Debug Mode:** Set `GOOGLE_PERSONAL_MCP_DEBUG=1` to disable masking for troubleshooting.

### Retry Logic

Transient errors are retried automatically:

```python
from google_mcp_core.utils.retry import retry_on_rate_limit

@retry_on_rate_limit(max_retries=3, backoff_base=2)
def api_operation():
    return service.spreadsheets().values().get(...).execute()
```

Handles:
- Rate limit errors (429)
- Temporary network failures
- API quota errors

### Request ID Context

Each tool call gets a unique request ID for tracing:

```python
from google_mcp_core.utils.context import set_request_id, get_request_id, clear_request_id

@mcp.tool()
def tool_name(...):
    request_id = set_request_id()
    try:
        # ... operation
        return {"status": "success", "request_id": request_id}
    finally:
        clear_request_id()
```

Request IDs appear in:
- Tool responses
- Audit logs
- Structured logs
- Error messages

## Logging Architecture

### Structured Logging

JSON-formatted logs for machine parsing:

```python
from google_mcp_core.logging.structured import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", extra={
    "request_id": request_id,
    "spreadsheet_id": sheet_id,
    "range": range_name
})
```

Enable: `GOOGLE_PERSONAL_MCP_JSON_LOGS=1`

### Audit Logging

Separate audit trail for all tool calls:

```python
from google_mcp_core.logging.audit import get_audit_logger

audit_logger = get_audit_logger()
audit_logger.log_tool_call(
    tool_name="read_cells",
    parameters={"sheet_alias": "prompts", "range": "A1:B10"},
    request_id=request_id,
    success=True
)
```

Audit logs stored at: `~/.config/google-personal-mcp/audit.log`

View: `tail -f ~/.config/google-personal-mcp/audit.log | jq .`

## Performance Considerations

### Service Caching

Google API services are expensive to create. `GoogleContext` caches them:

- **First call:** Creates service (~100-200ms)
- **Subsequent calls:** Reuses cached instance (~1ms)

### Credential Reuse

Credentials are lazy-loaded and cached per `GoogleContext`:

- Single credential load per profile per session
- Automatic token refresh
- No redundant OAuth flows

### Batch Operations

Where possible, use batch APIs:

```python
# Bad: Multiple round trips
for row in rows:
    service.append_row(sheet_id, range, row)

# Good: Single batch request
service.batch_update(sheet_id, requests=[
    {"appendCells": {"rows": rows}}
])
```

## Security Considerations

### Access Control

- **Drive operations:** Restricted to configured `folder_ids`
- **Sheets operations:** No built-in restrictions (controlled by OAuth scopes)
- **Configuration:** Stored in user directory with restricted permissions

### Credential Storage

- **Location:** `~/.config/google-personal-mcp/profiles/<name>/`
- **Permissions:** User-only read/write (600)
- **Git ignore:** All credential files excluded
- **Masking:** Credentials redacted from logs and errors

### OAuth Best Practices

- Desktop app OAuth flow (not web)
- Local token storage only
- No token sharing between profiles
- Automatic token refresh
- Graceful re-authentication on failure

## Agent Kernel Integration

This architecture extends the Agent Kernel reference architecture. See:

- [Agent Kernel Reference Architecture](system-prompts/reference-architecture.md)

**Project-Specific Extensions:**
- MCP server layer
- Google API integration layer
- Profile-based authentication
- Resource alias system
- CLI tool architecture

## See Also

- [AGENTS.md](../AGENTS.md) - Core workflow
- [Definition of Done](definition-of-done.md) - Quality standards
- [Implementation Reference](implementation-reference.md) - Implementation patterns
- [Development Guide](development.md) - Detailed development practices

---
Last Updated: 2026-01-27
