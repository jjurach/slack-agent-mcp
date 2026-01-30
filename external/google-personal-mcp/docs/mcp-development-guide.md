# MCP Server Development & Debugging Guide

## Part 1: Understanding the MCP Server Architecture

### Project Structure
```
google-personal-mcp/
├── src/
│   ├── google_mcp_core/          # Core library (reusable)
│   │   ├── auth.py               # OAuth2 authentication
│   │   ├── config.py             # Configuration management
│   │   ├── context.py            # GoogleContext (service facade)
│   │   ├── sheets.py             # Google Sheets API wrapper
│   │   ├── drive.py              # Google Drive API wrapper
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── logging/              # Logging infrastructure
│   │   ├── utils/                # Utilities (retry, sanitizer, context)
│   │   └── cli.py                # CLI commands
│   │
│   └── google_personal_mcp/      # MCP server (entry point)
│       └── server.py             # FastMCP server + tool definitions
│
├── tests/                        # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_*.py                # Unit/integration tests
│
├── docs/                        # Documentation
│   ├── development.md           # Development guide
│   ├── troubleshooting.md       # Common issues
│   └── phase1-implementation.md # What was implemented
│
├── pyproject.toml               # Project metadata + tool configs
├── requirements.txt             # Pinned dependencies
├── requirements-dev.txt         # Dev dependencies
└── .env.example                 # Environment template
```

### Key Components

**GoogleContext (src/google_mcp_core/context.py)**
- Lazy-loads Google API credentials
- Caches authenticated service instances
- Handles token refresh automatically

**SheetsService & DriveService**
- Wrappers around Google APIs
- Handle API pagination and error cases
- Support retry logic

**ConfigManager**
- Loads config.json with profiles
- Environment-based config loading
- .env file support

**MCP Server (src/google_personal_mcp/server.py)**
- Registers tools as MCP resources
- Handles tool invocation
- Implements request ID tracking
- Logs all operations to audit trail

## Part 2: Development Workflow

### Setup Development Environment

```bash
# 1. Clone and enter directory
cd /home/phaedrus/AiSpace/google-personal-mcp

# 2. Create virtual environment (if needed)
python3 -m venv venv
source venv/bin/activate

# 3. Install development dependencies
pip install -e ".[dev]"
pip install -r requirements-dev.txt
```

### Running the Server

#### Option A: Direct Python (for debugging)
```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
python -m google_personal_mcp.server
```

#### Option B: As MCP server (with client)
```bash
google-personal-mcp
```

#### Option C: With custom config
```bash
export GOOGLE_MCP_ENV=dev
export GOOGLE_PERSONAL_MCP_CONFIG=/path/to/config.dev.json
python -m google_personal_mcp.server
```

### Common Development Tasks

#### Add a New Tool

1. **Implement business logic** in service class (sheets.py or drive.py):
```python
# In src/google_mcp_core/sheets.py
class SheetsService:
    def append_rows(self, spreadsheet_id: str, range_name: str, rows: List[List]):
        """Append multiple rows to sheet."""
        body = {"values": rows}
        return self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
```

2. **Register as MCP tool** (server.py):
```python
@mcp.tool()
def append_rows(sheet_alias: str, range_name: str, rows: List[List[str]]) -> dict:
    """Append multiple rows to a sheet."""
    request_id = set_request_id()
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        result = service.append_rows(spreadsheet_id, range_name, rows)

        audit_logger.log_tool_call(
            tool_name="append_rows",
            parameters={"sheet_alias": sheet_alias, "range_name": range_name},
            success=True
        )

        return {"status": "success", "data": result, "request_id": request_id}
    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)
        audit_logger.log_tool_call(
            tool_name="append_rows",
            parameters={"sheet_alias": sheet_alias},
            success=False,
            error_message=error_msg
        )
        return {"status": "error", "message": error_msg, "request_id": request_id}
    finally:
        clear_request_id()
```

3. **Write tests** (tests/test_sheets_service.py):
```python
def test_append_rows(mock_sheets_service):
    service = SheetsService(mock_google_context)
    result = service.append_rows("sheet_id", "Sheet1!A:B", [["col1", "col2"]])
    assert result is not None
```

## Part 3: Debugging Techniques

### 1. Enable Verbose Logging

```bash
# All levels
export GOOGLE_PERSONAL_MCP_VERBOSE=1

# JSON format (for log aggregation)
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1

# Debug mode (disables credential masking)
export GOOGLE_PERSONAL_MCP_DEBUG=1

# Run server
python -m google_personal_mcp.server 2>&1 | tee server.log
```

### 2. Inspect Audit Log

```bash
# Real-time audit log
tail -f ~/.config/google-personal-mcp/audit.log | jq .

# Pretty print recent entries
tail -n 10 ~/.config/google-personal-mcp/audit.log | jq .

# Filter by tool name
cat ~/.config/google-personal-mcp/audit.log | jq 'select(.tool_name=="list_configured_sheets")'

# Filter by errors
cat ~/.config/google-personal-mcp/audit.log | jq 'select(.success==false)'
```

### 3. Test Specific Component

```bash
# Test authentication
python -c "
from google_mcp_core.auth import AuthManager
auth = AuthManager(profile='default')
print('Profile: default')
print(f'Credentials: {auth.get_credentials()}')
"

# Test config loading
python -c "
from google_mcp_core.config import ConfigManager
config = ConfigManager()
print('Sheets:', list(config.config.sheets.keys()))
print('Folders:', list(config.config.drive_folders.keys()))
"

# Test specific service
python -c "
from google_mcp_core.context import GoogleContext
from google_mcp_core.sheets import SheetsService
ctx = GoogleContext(profile='default')
sheets = SheetsService(ctx)
titles = sheets.list_sheet_titles('YOUR_SHEET_ID')
print(f'Sheet titles: {titles}')
"
```

### 4. Add Debug Breakpoints

```python
# In server.py tool function
@mcp.tool()
def list_configured_sheets() -> dict:
    """List all configured sheets."""
    import pdb; pdb.set_trace()  # Breakpoint - server will pause here

    request_id = set_request_id()
    # ... rest of code
```

Run with: `python -m google_personal_mcp.server` (will drop into pdb)

### 5. Mock External Dependencies

```python
# In tests/conftest.py
from unittest.mock import MagicMock

@pytest.fixture
def mock_google_context(monkeypatch):
    """Mock GoogleContext to avoid real API calls."""
    mock_ctx = MagicMock()
    mock_ctx.credentials = MagicMock()
    mock_ctx.get_service = MagicMock(return_value=MagicMock())
    return mock_ctx

# Use in tests
def test_with_mock(mock_google_context):
    service = SheetsService(mock_google_context)
    # Now service uses mocked context, no real API calls
```

## Part 4: Common Issues & Solutions

### Issue: "credentials.json not found"

**Diagnosis:**
```bash
# Check where server looks for credentials
ls -la ~/.config/google-personal-mcp/profiles/default/

# Check if GOOGLE_PERSONAL_CREDENTIALS_JSON is set
echo $GOOGLE_PERSONAL_CREDENTIALS_JSON
```

**Fix:**
```bash
# Option 1: Use environment variable
export GOOGLE_PERSONAL_CREDENTIALS_JSON='{"type":"service_account",...}'

# Option 2: Download from Google Cloud Console
# 1. Go to https://console.cloud.google.com
# 2. APIs & Services > Credentials
# 3. Download OAuth 2.0 Client ID JSON
# 4. Save to ~/.config/google-personal-mcp/profiles/default/credentials.json

mkdir -p ~/.config/google-personal-mcp/profiles/default
cp ~/Downloads/client_secret_*.json ~/.config/google-personal-mcp/profiles/default/credentials.json
```

### Issue: "Token expired or invalid scopes"

**Diagnosis:**
```bash
# Check token file
cat ~/.config/google-personal-mcp/profiles/default/token.json | jq '.expires_in'

# Check if scopes are sufficient
cat ~/.config/google-personal-mcp/profiles/default/token.json | jq '.scope'
```

**Fix:**
```bash
# Delete token to force re-authentication
rm ~/.config/google-personal-mcp/profiles/default/token.json

# Server will re-authenticate on next run
python -m google_personal_mcp.server
```

### Issue: "Sheet alias 'prompts' not found"

**Diagnosis:**
```bash
# Check config
cat ~/.config/google-personal-mcp/config.json | jq '.sheets'

# Check which profiles exist
ls -la ~/.config/google-personal-mcp/profiles/
```

**Fix:**
```bash
# Create config
mkdir -p ~/.config/google-personal-mcp
cat > ~/.config/google-personal-mcp/config.json << 'EOC'
{
  "sheets": {
    "prompts": {
      "id": "YOUR_SPREADSHEET_ID",
      "profile": "default",
      "description": "Main prompts"
    }
  },
  "drive_folders": {}
}
EOC

# Get spreadsheet ID from URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

### Issue: "Import error: No module named 'google_mcp_core'"

**Diagnosis:**
```bash
# Check if installed in editable mode
pip show google-personal-mcp

# Check PYTHONPATH
echo $PYTHONPATH
```

**Fix:**
```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/home/phaedrus/AiSpace/google-personal-mcp/src:$PYTHONPATH
```

## Part 5: Testing Workflow

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_config.py -v
```

### Run specific test
```bash
pytest tests/test_config.py::TestLoadEnvFile::test_load_env_file_basic -v
```

### Run with coverage
```bash
pytest tests/ --cov=src/google_mcp_core --cov-report=term-missing
```

### Run with debugging
```bash
pytest tests/test_config.py -v -s  # -s shows print statements
pytest tests/test_config.py -v --pdb  # Drop into debugger on failure
```

### Write new test

```python
# tests/test_my_feature.py
import pytest
from google_mcp_core.sheets import SheetsService

def test_new_feature(mock_google_context):
    """Test the new feature."""
    service = SheetsService(mock_google_context)
    result = service.new_method()
    assert result is not None
```

## Part 6: Code Quality Checks

### Format code
```bash
black src/ tests/
```

### Check for issues
```bash
ruff check src/
```

### Type checking
```bash
mypy src/
```

### Lint
```bash
pylint src/
```

### All checks
```bash
./scripts/check-all.sh  # if exists, or manually run all above
```

## Part 7: Debugging Checklist

When something breaks:

- [ ] Check error message in console output
- [ ] Enable verbose logging: `export GOOGLE_PERSONAL_MCP_VERBOSE=1`
- [ ] Check audit log: `tail -f ~/.config/google-personal-mcp/audit.log | jq .`
- [ ] Check server logs: `tail -f server.log`
- [ ] Verify configuration: `cat ~/.config/google-personal-mcp/config.json`
- [ ] Check credentials exist: `ls -la ~/.config/google-personal-mcp/profiles/*/`
- [ ] Test component directly: `python -c "from google_mcp_core.sheets import SheetsService; ..."`
- [ ] Run relevant tests: `pytest tests/ -v -k keyword`
- [ ] Add debug print statement: `print(f"Debug: {variable}")` then `pytest -s`
- [ ] Use pdb: `import pdb; pdb.set_trace()`

## Part 8: Deployment Debugging

### In production/container:

```bash
# Using environment variables only (no files)
export GOOGLE_PERSONAL_CREDENTIALS_JSON='{"type":"service_account",...}'
export GOOGLE_PERSONAL_TOKEN_JSON='{"access_token":"ya29...",...}'

# Enable JSON logging for log aggregation
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1

# Start server
python -m google_personal_mcp.server

# Collect logs
docker logs container_name | jq .
```

---

This guide covers the complete development lifecycle. Start with understanding the architecture, then practice adding features, then debug issues using the techniques provided.
