# Project Workflows

This document describes development workflows specific to the Google Personal MCP Server project.

## Core Agent Workflow

All AI agents working on this project must follow the **A-E workflow** defined in [AGENTS.md](../AGENTS.md):

- **A: Analyze** - Understand the request and declare intent
- **B: Build** - Create project plan
- **C: Code** - Implement the plan
- **D: Document** - Update documentation
- **E: Evaluate** - Verify against Definition of Done

For complete workflow documentation, see the [Agent Kernel Workflows](system-prompts/workflows/).

## MCP Tool Development Workflow

When adding a new MCP tool to the server:

### 1. Analyze & Plan (Steps A-B)

- Identify which Google API is needed
- Check if OAuth scopes are sufficient
- Determine input/output schema
- Plan service layer changes
- Document expected behavior

### 2. Implement Service Layer (Step C)

```python
# In src/google_mcp_core/sheets.py (or appropriate service)
class SheetsService:
    def new_operation(self, spreadsheet_id: str, param: str):
        """Implement the operation at service layer."""
        # Google API calls here
        return result
```

**Service layer principles:**
- Thin wrapper around Google APIs
- Minimal business logic
- Return raw or lightly processed responses
- No MCP-specific code

### 3. Implement Tool Layer (Step C)

```python
# In src/google_personal_mcp/server.py
@mcp.tool()
def new_tool(alias: str, param: str) -> dict:
    """MCP tool implementation."""
    request_id = set_request_id()
    try:
        service, resource_id = get_sheets_service(alias)
        result = service.new_operation(resource_id, param)

        audit_logger.log_tool_call(...)
        return {"status": "success", "result": result, "request_id": request_id}

    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)
        audit_logger.log_tool_call(..., success=False, error_message=error_msg)
        return {"status": "error", "message": error_msg, "request_id": request_id}

    finally:
        clear_request_id()
```

**Tool layer principles:**
- Follow standard tool template (see [Implementation Reference](implementation-reference.md))
- Request ID management
- Structured error handling
- Credential masking
- Audit logging

### 4. Add Tests (Step C)

Create both unit and integration tests:

```python
# Unit test - tests/unit/test_sheets_service.py
def test_new_operation(mock_sheets_service):
    """Test new operation with mocked API."""
    result = mock_sheets_service.new_operation("sheet_id", "param")
    assert result is not None

# Integration test - tests/integration/test_sheets_integration.py
@pytest.mark.integration
def test_new_operation_integration():
    """Test new operation with real API."""
    service = SheetsService(GoogleContext())
    result = service.new_operation(TEST_SHEET_ID, "param")
    assert result is not None
```

### 5. Add CLI Command (Optional, Step C)

If the tool should be accessible via CLI:

```python
# In src/google_mcp_core/cli.py
def cmd_new_command(args):
    """CLI command handler."""
    service, resource_id = get_sheets_service(args.alias)
    result = service.new_operation(resource_id, args.param)
    print(f"Success: {result}")

# Register in COMMANDS dict
COMMANDS = {
    "sheets": {
        "new-command": {
            "handler": cmd_new_command,
            "help": "Description of command",
            "args": [
                {"name": "alias", "help": "Sheet alias"},
                {"name": "param", "help": "Parameter description"}
            ]
        }
    }
}
```

### 6. Update Documentation (Step D)

- Add tool to README.md tool list
- Update architecture.md if architectural changes
- Add examples to implementation-reference.md if introducing new patterns

### 7. Verify Quality (Step E)

Check against [Definition of Done](definition-of-done.md):

- [ ] Service method implemented
- [ ] MCP tool follows standard template
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing (if applicable)
- [ ] CLI command added (if applicable)
- [ ] Audit logging integrated
- [ ] Credential masking working
- [ ] Documentation updated
- [ ] No credential leakage in errors or logs

## Google API Integration Workflow

When adding support for a new Google API:

### 1. Plan the Integration (Steps A-B)

- Identify required OAuth scopes
- Review Google API documentation
- Plan service class design
- Identify rate limits and quotas
- Plan error handling strategy

### 2. Update OAuth Scopes (Step C)

```python
# In src/google_mcp_core/auth.py
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",  # NEW
]
```

**Note:** Users must re-authenticate when scopes change:

```bash
rm ~/.config/google-personal-mcp/profiles/*/token.json
```

### 3. Create Service Class (Step C)

```python
# In src/google_mcp_core/gmail.py (new file)
from google_mcp_core.context import GoogleContext

class GmailService:
    """Wrapper for Gmail API operations."""

    def __init__(self, context: GoogleContext):
        self.context = context
        self.service = context.get_service("gmail", "v1")

    def list_messages(self, query: str = "") -> List[Dict]:
        """List messages matching query."""
        return self.service.users().messages().list(
            userId="me",
            q=query
        ).execute().get("messages", [])
```

### 4. Add Service Locator (Step C)

```python
# In src/google_personal_mcp/server.py
def get_gmail_service(profile: str = "default") -> GmailService:
    """Get GmailService instance for profile."""
    context = GoogleContext(profile=profile)
    return GmailService(context)
```

### 5. Add MCP Tools (Step C)

Follow the standard MCP tool template using the new service.

### 6. Add Diagnostic CLI Commands (Step C)

```python
# In src/google_mcp_core/cli.py
def cmd_gmail_list(args):
    """List Gmail messages."""
    service = get_gmail_service(args.profile)
    messages = service.list_messages(args.query)
    for msg in messages:
        print(f"- {msg['id']}")

COMMANDS = {
    "gmail": {  # New command group
        "list": {
            "handler": cmd_gmail_list,
            "help": "List Gmail messages",
            "args": [
                {"name": "query", "help": "Search query"},
                {"name": "--profile", "default": "default", "help": "Profile name"}
            ]
        }
    }
}
```

### 7. Document the Integration (Step D)

- Update README.md with new OAuth scope
- Document new service in architecture.md
- Add integration examples to implementation-reference.md
- Update CHANGELOG if present

### 8. Verify Integration (Step E)

- [ ] OAuth scopes updated
- [ ] Service class implemented
- [ ] Service locator added
- [ ] MCP tools implemented
- [ ] Tests written (unit + integration)
- [ ] CLI commands added
- [ ] Documentation updated
- [ ] Re-authentication tested
- [ ] Rate limiting handled

## Testing Workflow

### Running Tests Locally

```bash
# Unit tests only (fast, no API calls)
pytest tests/unit/ -v

# Integration tests (requires credentials)
pytest tests/integration/ -v -m integration

# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src/google_mcp_core --cov-report=term-missing

# Watch mode (re-run on file changes)
pytest-watch tests/
```

### Test-Driven Development (TDD)

For complex features, consider TDD:

1. **Write failing test** - Define expected behavior
2. **Implement minimum code** - Make test pass
3. **Refactor** - Improve code quality
4. **Repeat** - Next test case

### Google API Mocking

All tests use mocked Google APIs by default:

```python
# tests/conftest.py provides fixtures
def test_operation(mock_sheets_service):
    """Test uses mocked service, no real API calls."""
    result = mock_sheets_service.operation()
    assert result is not None
```

**Integration tests opt-in to real APIs:**

```python
@pytest.mark.integration
@pytest.mark.skipif(not has_credentials(), reason="Requires credentials")
def test_operation_integration():
    """This test makes real API calls."""
    service = SheetsService(GoogleContext())
    result = service.operation()
    assert result is not None
```

## Configuration Management Workflow

### Adding Resource Aliases

Users can add resource aliases via CLI:

```bash
# Add sheet alias
google-personal-mcp config add-sheet prompts 1ABC123XYZ --profile=default

# Add drive folder
google-personal-mcp config add-folder documents 1XYZ789ABC --profile=work
```

Or manually edit `~/.config/google-personal-mcp/config.json`:

```json
{
  "sheets": {
    "new-alias": {
      "id": "1ABC...",
      "profile": "default",
      "description": "Description"
    }
  }
}
```

### Profile Management

Create new authentication profiles:

```bash
# Create profile directory
mkdir -p ~/.config/google-personal-mcp/profiles/work

# Add credentials for that profile
cp ~/Downloads/work_credentials.json ~/.config/google-personal-mcp/profiles/work/credentials.json

# Tools automatically use profile from resource config
```

## Debugging Workflow

### Enable Verbose Logging

```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
export GOOGLE_PERSONAL_MCP_DEBUG=1  # Disables credential masking

python -m google_personal_mcp.server
```

### Monitor Audit Log

```bash
# Real-time monitoring
tail -f ~/.config/google-personal-mcp/audit.log | jq .

# Filter by tool
cat audit.log | jq 'select(.tool_name=="read_cells")'

# Filter by errors
cat audit.log | jq 'select(.success==false)'
```

### Test Components Directly

```bash
# Test authentication
python -c "
from google_mcp_core.context import GoogleContext
ctx = GoogleContext(profile='default')
print(ctx.credentials)
"

# Test service
python -c "
from google_mcp_core.sheets import SheetsService
from google_mcp_core.context import GoogleContext
service = SheetsService(GoogleContext())
print(service.list_sheet_titles('SHEET_ID'))
"
```

### Debug with Breakpoints

```python
# In code
import pdb; pdb.set_trace()

# Or use IDE debugger
# VSCode: Add breakpoint, press F5
```

## Troubleshooting Common Issues

### Authentication Failures

```bash
# Delete token to force re-authentication
rm ~/.config/google-personal-mcp/profiles/default/token.json

# Verify credentials exist
ls -la ~/.config/google-personal-mcp/profiles/default/credentials.json

# Test authentication directly
python -c "from google_mcp_core.auth import AuthManager; AuthManager().get_credentials()"
```

### Configuration Errors

```bash
# Validate config syntax
cat ~/.config/google-personal-mcp/config.json | jq .

# Check resource aliases
google-personal-mcp config show
```

### API Errors

- Enable verbose logging to see full error details
- Check audit log for error patterns
- Verify OAuth scopes are sufficient
- Check Google Cloud Console for API quota limits

## See Also

- [AGENTS.md](../AGENTS.md) - Core A-E workflow
- [Definition of Done](definition-of-done.md) - Quality checklist
- [Architecture](architecture.md) - System design
- [Implementation Reference](implementation-reference.md) - Code patterns
- [Agent Kernel Workflows](system-prompts/workflows/) - Complete workflow documentation

---
Last Updated: 2026-01-27
