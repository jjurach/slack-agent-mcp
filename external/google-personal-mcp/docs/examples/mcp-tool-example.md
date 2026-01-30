# Example: Adding a New MCP Tool

This document provides a complete walkthrough of adding a new MCP tool to the Google Personal MCP Server.

## Scenario

Add a tool to append a row to a Google Sheet.

**Tool Requirements:**
- Name: `append_row`
- Parameters: `sheet_alias` (string), `range_name` (string), `values` (list of strings)
- Returns: Success/error response with request ID
- Follows standard tool template

## Step 1: Implement Service Layer Method

**File:** `src/google_mcp_core/sheets.py`

```python
from typing import List, Any, Dict

class SheetsService:
    # ... existing methods ...

    def append_row(self, spreadsheet_id: str, range_name: str, values: List[Any]) -> Dict[str, Any]:
        """
        Append a row to a sheet.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The A1 notation range (e.g., "Sheet1!A:Z")
            values: List of values to append

        Returns:
            API response with updated range and values

        Raises:
            HttpError: If API request fails
        """
        body = {"values": [values]}

        return self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
```

**Why service layer first?**
- Separates business logic from MCP protocol
- Makes testing easier
- Service can be reused by CLI and other tools

## Step 2: Add MCP Tool

**File:** `src/google_personal_mcp/server.py`

```python
from typing import List
from fastmcp import FastMCP
from google_mcp_core.sheets import SheetsService
from google_mcp_core.utils.context import set_request_id, clear_request_id
from google_mcp_core.utils.sanitizer import mask_credentials, should_sanitize
from google_mcp_core.logging.audit import get_audit_logger

audit_logger = get_audit_logger()

@mcp.tool()
def append_row(sheet_alias: str, range_name: str, values: List[str]) -> dict:
    """
    Append a row of values to a Google Sheet.

    Adds a new row at the end of the specified range in the sheet identified
    by the alias. Values are entered as if typed by a user (numbers, dates,
    and formulas are parsed).

    Args:
        sheet_alias: Alias of the sheet (from config)
        range_name: A1 notation range (e.g., "Sheet1!A:Z")
        values: List of values to append (e.g., ["Name", "Email", "2024-01-15"])

    Returns:
        dict: Response with status, updated range info, and request_id
              {
                  "status": "success",
                  "result": {
                      "updates": {
                          "updatedRange": "Sheet1!A10:C10",
                          "updatedRows": 1,
                          "updatedColumns": 3
                      }
                  },
                  "request_id": "abc-123-def"
              }
    """
    request_id = set_request_id()

    try:
        # Get service instance and resource ID
        service, spreadsheet_id = get_sheets_service(sheet_alias)

        # Perform operation
        result = service.append_row(spreadsheet_id, range_name, values)

        # Log success
        audit_logger.log_tool_call(
            tool_name="append_row",
            parameters={
                "sheet_alias": sheet_alias,
                "range_name": range_name,
                "num_values": len(values)
            },
            request_id=request_id,
            success=True
        )

        # Return success response
        return {
            "status": "success",
            "result": result,
            "request_id": request_id
        }

    except Exception as e:
        # Mask credentials in error message
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)

        # Log error
        audit_logger.log_tool_call(
            tool_name="append_row",
            parameters={
                "sheet_alias": sheet_alias,
                "range_name": range_name
            },
            request_id=request_id,
            success=False,
            error_message=error_msg
        )

        # Return error response
        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id
        }

    finally:
        # Always clear request context
        clear_request_id()
```

**Key implementation details:**
1. **Request ID**: `set_request_id()` at start, `clear_request_id()` in finally
2. **Service locator**: `get_sheets_service(alias)` handles config lookup
3. **Error handling**: Broad `except Exception` catches all errors
4. **Credential masking**: `mask_credentials()` prevents leaks
5. **Audit logging**: Log both success and failure
6. **Structured response**: Always return dict with status and request_id

## Step 3: Write Unit Tests

**File:** `tests/test_sheets_service.py`

```python
import pytest
from unittest.mock import MagicMock
from google_mcp_core.sheets import SheetsService

def test_append_row(mock_google_context):
    """Test appending a row to a sheet."""
    # Arrange - setup service and mock response
    service = SheetsService(mock_google_context)

    mock_response = {
        "updates": {
            "updatedRange": "Sheet1!A10:C10",
            "updatedRows": 1,
            "updatedColumns": 3,
            "updatedCells": 3
        }
    }

    # Configure mock to return our response
    mock_service = service.service.spreadsheets().values().append
    mock_service.return_value.execute.return_value = mock_response

    # Act - call the method
    result = service.append_row(
        spreadsheet_id="test_sheet_id",
        range_name="Sheet1!A:C",
        values=["Alice", "alice@example.com", "2024-01-15"]
    )

    # Assert - verify result and mock was called correctly
    assert result == mock_response
    assert result["updates"]["updatedRows"] == 1

    # Verify API was called with correct parameters
    mock_service.assert_called_once()
    call_kwargs = mock_service.call_args[1]
    assert call_kwargs["spreadsheetId"] == "test_sheet_id"
    assert call_kwargs["range"] == "Sheet1!A:C"
    assert call_kwargs["body"]["values"] == [["Alice", "alice@example.com", "2024-01-15"]]


def test_append_row_error_handling(mock_google_context):
    """Test error handling when append fails."""
    # Arrange - setup service to raise error
    service = SheetsService(mock_google_context)

    from googleapiclient.errors import HttpError
    from unittest.mock import Mock

    # Create mock HTTP error
    resp = Mock()
    resp.status = 404
    resp.reason = "Not Found"

    mock_service = service.service.spreadsheets().values().append
    mock_service.return_value.execute.side_effect = HttpError(resp, b"Sheet not found")

    # Act & Assert - verify exception is raised
    with pytest.raises(HttpError) as exc_info:
        service.append_row("bad_sheet_id", "Sheet1!A:C", ["value1", "value2"])

    assert "Sheet not found" in str(exc_info.value)
```

**Testing strategy:**
- Mock Google API responses using `mock_google_context` fixture
- Test happy path (successful append)
- Test error paths (API errors)
- Verify mock was called with correct parameters
- No real API calls in unit tests

## Step 4: Write Integration Test (Optional)

**File:** `tests/integration/test_sheets_integration.py`

```python
import pytest
import os
from google_mcp_core.context import GoogleContext
from google_mcp_core.sheets import SheetsService

@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.exists(os.path.expanduser("~/.config/google-personal-mcp/profiles/default/credentials.json")),
    reason="Requires credentials"
)
def test_append_row_integration():
    """Integration test with real Google Sheets API."""
    # Setup - use real context and service
    context = GoogleContext(profile="default")
    service = SheetsService(context)

    # Get test sheet ID from environment
    test_sheet_id = os.getenv("TEST_SPREADSHEET_ID")
    if not test_sheet_id:
        pytest.skip("TEST_SPREADSHEET_ID not set")

    # Act - append test row
    result = service.append_row(
        spreadsheet_id=test_sheet_id,
        range_name="TestSheet!A:C",
        values=["Integration Test", "test@example.com", "2024-01-27"]
    )

    # Assert - verify response structure
    assert "updates" in result
    assert result["updates"]["updatedRows"] == 1
    assert result["updates"]["updatedColumns"] == 3
```

**Integration test notes:**
- Marked with `@pytest.mark.integration`
- Skips if credentials not available
- Uses real Google API
- Requires test spreadsheet ID from environment
- Should clean up test data after execution

## Step 5: Add CLI Command (Optional)

**File:** `src/google_mcp_core/cli.py`

```python
def cmd_sheets_append_row(args):
    """Append a row to a sheet."""
    try:
        service, spreadsheet_id = get_sheets_service(args.alias)
        result = service.append_row(spreadsheet_id, args.range, args.values)

        print(f"✅ Row appended successfully")
        print(f"   Range: {result['updates']['updatedRange']}")
        print(f"   Rows updated: {result['updates']['updatedRows']}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

# Register in COMMANDS dictionary
COMMANDS = {
    "sheets": {
        # ... existing commands ...
        "append-row": {
            "handler": cmd_sheets_append_row,
            "help": "Append a row to a sheet",
            "args": [
                {"name": "alias", "help": "Sheet alias"},
                {"name": "range", "help": "A1 notation range (e.g., Sheet1!A:C)"},
                {"name": "values", "nargs": "+", "help": "Values to append"}
            ]
        }
    }
}
```

**CLI design notes:**
- Reuses service layer (no duplicate logic)
- User-friendly output with emoji
- Errors to stderr with exit code 1
- Help text auto-generated from config

## Step 6: Update Documentation

**File:** `README.md`

Add to the MCP Tools section:

```markdown
### append_row

Append a row of values to a Google Sheet.

**Parameters:**
- `sheet_alias` (string): Alias of the sheet from config
- `range_name` (string): A1 notation range (e.g., "Sheet1!A:Z")
- `values` (list of strings): Values to append

**Returns:**
- `status`: "success" or "error"
- `result`: Updated range info (if success)
- `request_id`: Unique request identifier

**Example:**
```python
result = append_row(
    sheet_alias="prompts",
    range_name="Sheet1!A:D",
    values=["2024-01-27", "New prompt", "user123", "published"]
)
```
```

## Step 7: Run Tests and Verify

```bash
# Format code
black src/ tests/

# Run linting
ruff check --fix src/ tests/

# Run unit tests
pytest tests/test_sheets_service.py::test_append_row -v
# Expected: PASSED

# Run all tests
pytest tests/ -v
# Expected: All tests pass

# Check coverage
pytest tests/ --cov=src/google_mcp_core --cov-report=term-missing
# Expected: New code covered

# Test CLI command
google-personal-mcp sheets append-row prompts "Sheet1!A:D" "Test" "Value" "2024-01-27"
# Expected: ✅ Row appended successfully
```

## Step 8: Commit

```bash
git add -A
git commit -m "feat: add append_row MCP tool

Implements tool to append rows to Google Sheets.

- Service layer: SheetsService.append_row()
- MCP tool: append_row with standard template
- Unit tests: test_append_row, test_append_row_error_handling
- CLI command: sheets append-row
- Documentation updated

All tests passing. Follows standard tool template pattern.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Checklist

Before marking this task as done:

- [ ] Service method implemented in SheetsService
- [ ] MCP tool follows standard template (request ID, audit logging, error handling)
- [ ] Unit tests written and passing
- [ ] Integration test written (optional but recommended)
- [ ] CLI command added (optional)
- [ ] Documentation updated (README.md)
- [ ] Code formatted with black
- [ ] Linting passes with ruff
- [ ] No credential leaks in code
- [ ] Commit message follows format

## See Also

- [Implementation Reference](../implementation-reference.md) - Standard tool template
- [Definition of Done](../definition-of-done.md) - Complete checklist
- [Architecture](../architecture.md) - System design

---
Last Updated: 2026-01-27
