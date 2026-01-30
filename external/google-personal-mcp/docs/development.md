# Development Guide

This guide covers the architecture, design patterns, and development practices for the Google Personal MCP Server.

## Architecture Overview

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

## Key Design Patterns

### 1. Service Locator Pattern

```python
def get_sheets_service(alias: str) -> Tuple[SheetsService, str]:
    """Get service and resource ID from alias."""
    resource = config_manager.get_sheet_resource(alias)
    context = GoogleContext(profile=resource.profile)
    return SheetsService(context), resource.id
```

Centralizes service instantiation, handles configuration lookup.

### 2. Context Object Pattern

```python
class GoogleContext:
    """Lazy-loads credentials and caches service instances."""

    @property
    def credentials(self):
        if not self._creds:
            self._creds = self.auth_manager.get_credentials(...)
        return self._creds

    def get_service(self, service_name: str, version: str):
        if key not in self._services:
            self._services[key] = build(...)
        return self._services[key]
```

Lazy-loads and caches Google API services.

### 3. Access Control at Service Layer

```python
class DriveService:
    def _verify_access(self, parent_id: str):
        if parent_id not in self.allowed_folder_ids:
            raise AccessDeniedError(...)
```

All Drive operations validated against configured folder list.

### 4. Error Handling Pattern

```python
@mcp.tool()
def tool_name(...) -> dict:
    try:
        result = do_work(...)
        return {"status": "success", "data": result, "request_id": request_id}
    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)
        return {"status": "error", "message": error_msg, "request_id": request_id}
```

All tools catch exceptions, return structured errors, mask credentials.

## Adding New Tools

### Step 1: Implement Business Logic

Add a method to the appropriate service class (SheetsService, DriveService):

```python
# In src/google_mcp_core/sheets.py
class SheetsService:
    def append_row(self, spreadsheet_id: str, range_name: str, values: List[Any]):
        """Append row to sheet."""
        body = {"values": [values]}
        return self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
```

### Step 2: Add MCP Tool Definition

```python
# In src/google_personal_mcp/server.py
@mcp.tool()
def append_row(sheet_alias: str, range_name: str, values: List[str]) -> dict:
    """Append a row to a sheet."""
    request_id = set_request_id()
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        result = service.append_row(spreadsheet_id, range_name, values)

        audit_logger.log_tool_call(
            tool_name="append_row",
            parameters={"sheet_alias": sheet_alias, "range_name": range_name},
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
            tool_name="append_row",
            parameters={"sheet_alias": sheet_alias, "range_name": range_name},
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

### Step 3: Add Tests

```python
# In tests/test_sheets_service.py
def test_append_row(mock_sheets_service):
    """Test appending a row."""
    service = SheetsService(mock_google_context)
    result = service.append_row("sheet_id", "Sheet1!A:B", ["col1", "col2"])
    assert result is not None

# In tests/
def test_append_row_tool(mock_sheets_service, monkeypatch):
    """Test append_row MCP tool."""
    # Setup mocks
    # Call tool
    # Assert response structure
```

## Adding New Scopes

If you add support for new Google APIs (Gmail, Calendar, etc.):

1. **Update default scopes** in `auth.py`:
   ```python
   scopes = [
       "https://www.googleapis.com/auth/spreadsheets",
       "https://www.googleapis.com/auth/drive",
       "https://www.googleapis.com/auth/gmail.readonly",  # New
   ]
   ```

2. **Create new service class**:
   ```python
   class GmailService:
       def __init__(self, context: GoogleContext):
           self.service = context.get_service("gmail", "v1")
   ```

3. **Add CLI commands** for diagnostics

4. **Document scopes** in README

## Testing Patterns

### Unit Tests with Mocks

```python
def test_list_sheets(mock_sheets_service, monkeypatch):
    """Test sheets listing with mocks."""
    # Setup
    mock_sheets_service.list_sheet_titles.return_value = ['Sheet1', 'Sheet2']

    # Execute
    service = SheetsService(mock_google_context)
    titles = service.list_sheet_titles("sheet_id")

    # Assert
    assert titles == ['Sheet1', 'Sheet2']
```

### Integration Tests

```python
@pytest.mark.skipif(not has_credentials(), reason="Requires credentials")
def test_list_sheets_integration():
    """Test sheets listing with real credentials."""
    context = GoogleContext(profile="default")
    service = SheetsService(context)
    titles = service.list_sheet_titles("YOUR_SHEET_ID")
    assert len(titles) > 0
```

### Security Tests

```python
def test_credential_masking():
    """Test that credentials are masked in errors."""
    error_msg = "Token: ya29.a0AfH6SMBx..."
    masked = mask_credentials(error_msg)
    assert "ya29" not in masked
    assert "***REDACTED***" in masked
```

## Debugging

### Enable Verbose Logging

```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
google-personal-mcp
```

### Debug Mode (Disables Credential Masking)

```bash
export GOOGLE_PERSONAL_MCP_DEBUG=1
```

### Check Audit Log

```bash
tail -f ~/.config/google-personal-mcp/audit.log | jq .
```

### Test Authentication

```bash
python -c "
from google_mcp_core.context import GoogleContext
ctx = GoogleContext(profile='default')
print(ctx.credentials)
"
```

## Performance Considerations

### Service Reuse

Google API services are cached in GoogleContext:
- First call: Creates service
- Subsequent calls: Reuses cached instance

### Token Refresh

Tokens are automatically refreshed when expired:
- No user intervention needed
- Transparent to callers
- Token saved to disk after refresh

### Retry Logic

Failed API calls are retried with exponential backoff:
- Configured in config.json
- Default: 3 retries, 2s initial delay, 2x backoff
- Only retries transient errors (5xx, 429)

## Security Considerations

### Credential Storage

- Stored in user's home directory: `~/.config/google-personal-mcp/profiles/{profile}/`
- File permissions: User-readable only
- Added to `.gitignore` to prevent accidental commits

### Scope Limitation

- Default scopes: Sheets API + Drive (app files only)
- Can be customized per tool/profile
- Validated before use

### Credential Masking

- File IDs, tokens, API keys masked in logs
- Disabled in debug mode (GOOGLE_PERSONAL_MCP_DEBUG=1)
- Applied to error messages returned to agents

### Audit Logging

- Records tool invocations (not credentials)
- Append-only log file
- Useful for compliance and troubleshooting

## Contributing Changes

1. Create a feature branch
2. Make changes following patterns above
3. Run tests: `pytest`
4. Run code quality: `ruff check`, `black --check`, `mypy`
5. Submit PR with clear description

See contributing.md for more details.
