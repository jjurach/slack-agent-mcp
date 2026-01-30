# MCP Server Implementation Guide

## Overview

This document provides a comprehensive guide to the Google Personal MCP Server implementation, focusing on Python libraries, configuration patterns, security mechanisms, testing strategies, and architectural decisions that make this an effective, maintainable MCP server.

## Table of Contents

1. [Core Architecture](#core-architecture)
2. [Python Libraries and Dependencies](#python-libraries-and-dependencies)
3. [Configuration System](#configuration-system)
4. [Authentication and Security](#authentication-and-security)
5. [Directory Structure](#directory-structure)
6. [Testing Strategy](#testing-strategy)
7. [CLI Integration](#cli-integration)
8. [Tool Design and Agent Effectiveness](#tool-design-and-agent-effectiveness)
9. [Logging and Observability](#logging-and-observability)
10. [Best Practices and Patterns](#best-practices-and-patterns)

---

## Core Architecture

### MCP Server Foundation

The server is built on the **FastMCP** framework (from the Anthropic MCP library), which provides:

- **Async/await support**: Built on `asyncio` for handling concurrent client connections
- **Tool registration**: Decorator-based tool registration via `@mcp.tool()`
- **Stdio communication**: Uses stdio for MCP protocol communication with clients
- **Type safety**: Argument validation through Python type hints

### Service-Oriented Design

The server follows a clean separation of concerns:

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

---

## Python Libraries and Dependencies

### Core Dependencies

#### MCP Protocol
- **`mcp`** (Anthropic MCP): Provides FastMCP server framework, async server infrastructure, and protocol handling
  - Reason: Official MCP implementation with first-class server support
  - Features: Type-safe tool definitions, async/await native, production-ready
  - Integration: Used for `FastMCP` class and `@mcp.tool()` decorator

#### Google APIs
- **`google-api-python-client`**: Official Google API client library
  - Reason: Mature, maintained by Google, comprehensive API coverage
  - Usage: Build Sheets v4 and Drive v3 service instances
  - Note: Uses "discovery" pattern—services built dynamically from Google's API specs

- **`google-auth-oauthlib`**: OAuth 2.0 authentication for installed applications
  - Reason: Official library for desktop OAuth flows (required for credentials.json approach)
  - Features: `InstalledAppFlow` class handles browser-based OAuth redirect
  - Key capability: Automatic token refresh without manual credential management

- **`google-auth`** (implicit dependency): Core authentication library
  - Provides `Credentials` classes, `GoogleRequest` for token refresh
  - Handles scope checking, token validity checking

#### Configuration & CLI
- **`cyclopts`**: Modern Python CLI framework
  - Why chosen: Type-hint driven, generates help automatically, supports subcommands
  - Alternative: Click, argparse (Cyclopts is more modern and Pythonic)
  - Usage: Powers the `google-personal` CLI command with subcommand groups (config, sheets, drive)

- **`pydantic`**: Data validation and configuration management
  - Used for: `ResourceConfig`, `AppConfig` models with automatic validation
  - Benefits: Runtime type validation, JSON serialization, clear schema definition
  - Integration: ConfigManager uses Pydantic to validate loaded JSON config

#### Async Support
- **`httpx`**: Modern async HTTP client (pulled in by dependencies)
- **`anyio`**: Async backend abstraction (used by FastMCP)
  - Allows running async code in sync contexts: `anyio.run(async_main)`

### Dependency Rationale

**Why these choices over alternatives?**

| Aspect | Choice | Why Not Alternative |
|--------|--------|-------------------|
| MCP Server | FastMCP | Custom impl would need protocol handling; Litestar/FastAPI over-engineered |
| Google Auth | google-auth-oauthlib | gcloud CLI auth is system-level; service accounts don't fit "personal" use case |
| Config Management | Pydantic | ConfigParser is untyped; YAML/TOML adds parsing complexity |
| CLI Framework | cyclopts | Argparse is verbose; Click requires decorators; cyclopts is modern & type-driven |

---

## Configuration System

### Profile-Based Credential Storage

The system supports multiple authentication profiles, enabling:
- **Multiple Google accounts** (personal, work, etc.)
- **Profile-specific tokens** (each profile has its own token.json)
- **Profile-specific scopes** (can request different permissions per profile)

### Directory Structure

```
~/.config/google-personal-mcp/
├── config.json                          # Resource aliases (sheets, folders)
└── profiles/
    ├── default/
    │   ├── credentials.json             # OAuth 2.0 client ID/secret
    │   └── token.json                   # Authorization token
    └── work/                            # Alternative profile
        ├── credentials.json
        └── token.json
```

**XDG Base Directory Compliance**: Uses `XDG_CONFIG_HOME` environment variable (default: `~/.config`), following Linux standards.

### Configuration Files

#### `config.json` - Resource Registry

```json
{
  "sheets": {
    "prompts": {
      "id": "1a2b3c4d5e6f7g8h9i0j...",
      "profile": "default",
      "description": "Main prompts storage"
    }
  },
  "drive_folders": {
    "documents": {
      "id": "folder_id_xyz",
      "profile": "default",
      "description": "Personal documents"
    }
  }
}
```

**Design Benefits:**
- Prevents IDs from appearing in tool output or agent context
- Agents use human-readable aliases (e.g., "prompts" instead of IDs)
- Profile mapping enables multi-account scenarios
- Description field provides agent context about resources

#### `credentials.json` - OAuth Client Secrets

Downloaded from Google Cloud Console. Contains:
- `client_id`: Public client identifier
- `client_secret`: Confidential credential (should never be in git)
- `auth_uri`, `token_uri`: OAuth endpoints

**Security:** Added to `.gitignore` to prevent accidental commits.

#### `token.json` - Authorization Token

Generated after first OAuth authentication. Contains:
- `access_token`: Short-lived token for API calls
- `refresh_token`: Long-lived token for obtaining new access tokens
- `expires_in`: Token expiration time
- `scopes`: Authorized permissions

**Security:**
- File is generated fresh per profile and scopes
- Never hardcoded
- Auto-refreshed transparently by google-auth library
- Added to `.gitignore`

### ConfigManager Class

```python
class ConfigManager:
    """Manages resource configuration and profile-based resource lookup."""

    def __init__(self, config_path: Optional[str] = None):
        """Load config from file or use defaults."""

    def get_sheet_resource(self, alias: str) -> ResourceConfig:
        """Return sheet config by alias, raise if not found."""

    def get_folder_resource(self, alias: str) -> ResourceConfig:
        """Return folder config by alias, raise if not found."""

    def get_allowed_folder_ids(self, profile: str) -> List[str]:
        """Return all folder IDs for a profile (used for access control)."""

    def list_sheets(self, profile: str) -> Dict[str, ResourceConfig]:
        """List all sheets, optionally filtered by profile."""

    def list_folders(self, profile: str) -> Dict[str, ResourceConfig]:
        """List all folders, optionally filtered by profile."""
```

**Key Methods for Tools:**
- `get_sheet_resource(alias)`: Validates alias exists, returns ID and profile
- `get_allowed_folder_ids(profile)`: Provides access control list for DriveService

### Pydantic Models

```python
class ResourceConfig(BaseModel):
    id: str                          # Google resource ID
    profile: str = "default"         # Profile name
    description: Optional[str]       # Human-readable purpose

class AppConfig(BaseModel):
    sheets: Dict[str, ResourceConfig]          # All sheet aliases
    drive_folders: Dict[str, ResourceConfig]   # All folder aliases
```

**Validation Benefits:**
- Type checking: IDs must be strings
- JSON serialization: Easy save/load
- Pydantic validates during load (catches malformed JSON early)

---

## Authentication and Security

### AuthManager Class

Handles credential lifecycle:

```python
class AuthManager:
    def get_credentials(self, profile: str, scopes: List[str]) -> Credentials:
        """
        1. Check if token.json exists and is valid
        2. If not valid or scopes missing: trigger OAuth2 flow
        3. Save new token to token.json
        4. Return Credentials object
        """
```

### OAuth 2.0 Flow

**First Run (No token.json):**
1. Read `credentials.json` (client ID/secret)
2. Trigger OAuth2 flow using `InstalledAppFlow.run_local_server()`
3. User clicks link, authenticates with Google account
4. OAuth redirect returns authorization code
5. Exchange code for access token and refresh token
6. Save token to `token.json`

**Subsequent Runs:**
1. Load token from `token.json`
2. If token is valid and has required scopes: use it directly
3. If token expired but refresh token exists: refresh automatically
4. If token invalid or scopes missing: repeat full OAuth flow

### Security Features

#### Scope Limitation

The server requests specific OAuth scopes:

```python
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",    # Sheets API
    "https://www.googleapis.com/auth/drive.file"       # Drive API (app files only)
]
```

**Why these scopes:**
- `spreadsheets`: Required for Sheets API access
- `drive.file`: Restricted to files created by this app (NOT all Drive files)
  - More secure than `drive.readonly` or `drive`
  - Prevents accidental access to all user files

#### Credential Storage

- **No embedding in code**: Credentials stored as files, not in environment variables or config
- **File permissions**: Config directory is user-owned and readable (`~/.config/google-personal-mcp/`)
- **Git safety**: Both `credentials.json` and `token.json` in `.gitignore`

#### Folder Access Control

The `DriveService` enforces folder restrictions:

```python
class DriveService:
    def __init__(self, context: GoogleContext, allowed_folder_ids: List[str]):
        self.allowed_folder_ids = allowed_folder_ids

    def _verify_access(self, file_id: str = None, parent_id: str = None):
        """Raise PermissionError if operation violates allowed_folder_ids."""
```

**Access Control Pattern:**
1. ConfigManager loads all folders for a profile from `config.json`
2. DriveService receives this list as `allowed_folder_ids`
3. Every file operation is validated against this list
4. Prevents agent from accessing folders outside configured set

#### Scope Checking

Before using a token, the server checks if it has required scopes:

```python
if creds and not creds.has_scopes(scopes):
    logger.info(f"Token exists but lacks required scopes. Re-authenticating...")
    # Trigger re-authentication
```

This handles cases where:
- User wants to elevate permissions (add new scopes)
- Token was generated with subset of scopes
- Different CLI commands request different scopes

### Secrets Management Best Practices

**What's implemented:**
- Credentials stored as files (not environment variables)
- Profile-based isolation (separate tokens per profile)
- Automatic token refresh (transparent to user)
- `.gitignore` prevents accidental commits

**What's NOT in this implementation (recommendations in checklist):**
- Credential encryption at rest
- Environment-based credential override
- Credential rotation policies
- Audit logging of credential usage

---

## Directory Structure

### Project Layout

```
google-personal-mcp/
├── src/
│   ├── google_personal_mcp/          # MCP server entry point
│   │   ├── __init__.py
│   │   └── server.py                 # FastMCP server, tool definitions
│   │
│   └── google_mcp_core/              # Shared libraries
│       ├── __init__.py
│       ├── auth.py                   # AuthManager class
│       ├── config.py                 # ConfigManager, Pydantic models
│       ├── context.py                # GoogleContext class
│       ├── sheets.py                 # SheetsService class
│       ├── drive.py                  # DriveService class
│       ├── cli.py                    # CLI commands (cyclopts)
│       └── scripts/
│           └── drive_tool.py         # Standalone diagnostic script
│
├── tests/
│   ├── __init__.py
│   ├── test_server.py                # Unit tests (mocks)
│   └── test_server_integration.py    # Integration tests (real server)
│
├── docs/
│   ├── mcp-implementation-guide.md   # This file
│   └── ...
│
├── pyproject.toml                    # Project metadata, dependencies
├── setup.py                          # Build script (if needed)
├── requirements.txt                  # Pinned dependencies (optional)
├── .gitignore                        # Excludes credentials, tokens, cache
├── README.md                         # User-facing setup instructions
└── main.py                           # Legacy entry point (for compatibility)
```

### Module Organization

**Why this structure?**

- `google_personal_mcp/`: MCP server package
  - Minimal, focused on FastMCP integration
  - Entry point for `google-personal-mcp` command

- `google_mcp_core/`: Reusable libraries
  - Can be imported by other tools/scripts
  - Not tied to MCP protocol
  - Easier to test in isolation

- `tests/`: Test suites
  - Parallel structure to `src/`
  - Unit tests mock external APIs
  - Integration tests use real server

**Benefits:**
- Reuse: `google_mcp_core` can be used by other MCP servers or CLI tools
- Clarity: Separation between "MCP integration" and "business logic"
- Testing: Core logic testable without MCP framework

---

## Testing Strategy

### Test Organization

#### Unit Tests (`tests/test_server.py`)

Tests the FastMCP server and tool registration:

```python
def test_server_instance(self):
    """Verify FastMCP server initialized."""

def test_get_tools(self):
    """Verify all expected tools registered."""

@patch('main.get_sheets_service')
def test_list_sheets(self, mock_get_sheets_service):
    """Test list_sheets tool with mocked service."""
```

**Approach:**
- Mock Google API services using `unittest.mock`
- Test tool registration and parameter validation
- No actual API calls (fast, deterministic)

**Limitations:**
- Doesn't catch integration issues
- Doesn't validate actual API interaction patterns

#### Integration Tests (`tests/test_server_integration.py`)

Tests the MCP server through the stdio interface:

```python
@pytest.mark.asyncio
async def test_server_initialization():
    """Start real server, verify initialization."""

@pytest.mark.asyncio
async def test_list_tools():
    """Query server for tool list."""

@pytest.mark.asyncio
async def test_list_sheets_tool():
    """Call list_sheets tool on real server."""
```

**Approach:**
- Use `StdioServerParameters` to start real server
- Use MCP `ClientSession` to call tools via protocol
- Actual server running (can fail if credentials missing)
- Uses pytest's asyncio support

**Benefits:**
- Tests actual MCP protocol communication
- Catches serialization issues
- Validates error handling end-to-end

**Requirements:**
- Credentials must be configured for tests to pass
- Google API quota might be consumed
- Tests are slower (network latency)

### Testing Patterns

**Pattern 1: Mocking Service Layer**

```python
@patch('server.get_sheets_service')
def test_list_sheets(self, mock_get_sheets_service):
    mock_service = MagicMock()
    mock_service.list_sheet_titles.return_value = ['Sheet1', 'Sheet2']
    mock_get_sheets_service.return_value = mock_service

    result = list_sheets_tool.fn(sheet_alias='test')
    assert result == ['Sheet1', 'Sheet2']
```

**Pattern 2: Testing Tool Parameters**

```python
tools = asyncio.run(mcp.get_tools())
list_sheets_tool = tools['list_sheets']

# Tool has proper schema
assert 'inputSchema' in list_sheets_tool
```

**Pattern 3: Integration Testing with Real Server**

```python
async with AsyncExitStack() as stack:
    stdio_transport = await stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()

    result = await session.call_tool("list_sheets", arguments={'sheet_alias': 'prompts'})
    assert result.content[0].text  # Tool returned result
```

### Test Coverage Gaps (Recommendations)

1. **Credential handling**: Unit tests for AuthManager (mocking OAuth)
2. **Config validation**: Unit tests for ConfigManager with invalid JSON
3. **Error scenarios**: Test tool behavior with missing aliases, invalid IDs
4. **Regression tests**: Add tests for each bug fix
5. **Security tests**: Test access control enforcement in DriveService

---

## CLI Integration

### CLI Framework: Cyclopts

The server provides a companion CLI for testing and diagnostics.

```bash
google-personal config list-sheets [--profile default]
google-personal drive list-files <folder_alias> [--profile default]
google-personal sheets list-tabs <sheet_alias> [--profile default]
google-personal sheets get-prompts <sheet_alias> <sheet_tab_name>
```

**Cyclopts Benefits:**

- **Type-driven**: Parameters from function signatures
- **Subcommands**: Natural grouping (config, drive, sheets)
- **Help generation**: Automatic from docstrings and type hints
- **Argument parsing**: No boilerplate decorators

### CLI Command Structure

```python
app = App(help_format="markdown")

config_app = App()
@config_app.command
def list_sheets(profile: str = "default"):
    """List all configured Google Sheets for a profile."""
    sheets = config_manager.list_sheets(profile)
    # Display formatted output

app.command(config_app, name="config")
app.command(drive_app, name="drive")
app.command(sheets_app, name="sheets")

def main():
    app()
```

### CLI as Configuration Tool

The CLI serves multiple purposes:

1. **Diagnostic**: Verify credentials and authentication
2. **Configuration**: Test config.json before using in server
3. **Manual operations**: Insert prompts, list files without MCP
4. **Development**: Easier to test than MCP protocol

### Bridging CLI and Server

Both CLI and server share:
- `ConfigManager`: Same config.json loading logic
- `GoogleContext`: Same authentication logic
- `SheetsService`, `DriveService`: Same API wrapper logic

**Benefit**: Changes to core logic automatically apply to both CLI and MCP server.

---

## Tool Design and Agent Effectiveness

### Tool Purpose

Each tool exposes Google API functionality for agents (Claude, Gemini, etc.) to use. Good tools should:

1. **Have clear purpose**: What does this tool do?
2. **Return useful data**: Can agents act on the results?
3. **Prevent accidents**: Are there safeguards?
4. **Provide context**: Do results include enough information?

### Tool Categories

#### Configuration Tools

**`list_configured_sheets(profile: str)`**
- Purpose: Discover available sheets
- Returns: List of aliases with IDs and descriptions
- Prevents: Agent doesn't need to know exact IDs
- Agent use: "What sheets do I have access to?"

**`list_configured_folders(profile: str)`**
- Purpose: Discover available Drive folders
- Returns: List of aliases with IDs and descriptions
- Prevents: Agent can't access arbitrary folders
- Agent use: "What Drive folders can I access?"

#### Sheets Tools

**`list_sheets(sheet_alias: str)`**
- Purpose: List tabs in a spreadsheet
- Returns: List of tab names
- Params: Uses alias (not raw ID)
- Agent use: "What tabs are in the prompts sheet?"

**`get_sheet_status(sheet_alias: str, range_name: str)`**
- Purpose: Read data from a range
- Returns: Cell values
- Default range: "README!A1" (table of contents)
- Agent use: "Show me what's in the README tab"

**`get_prompts(sheet_tab_name: str, sheet_alias: str)`**
- Purpose: Retrieve structured prompt data
- Returns: List of dictionaries with Name, Content, Created By, etc.
- Prevents: Agent sees normalized data, not raw cells
- Agent use: "Get all prompts from the 'Drafts' tab"

**`insert_prompt(sheet_tab_name: str, prompt_name: str, content: str, sheet_alias: str, author: str)`**
- Purpose: Add a new prompt
- Returns: Success/error status
- Timestamp: Automatically added
- Agent use: "Save this prompt to the prompts sheet"

#### Drive Tools

**`list_drive_files(folder_alias: str)`**
- Purpose: List files in a folder
- Returns: File metadata (ID, name, type)
- Access control: Only configured folders
- Agent use: "What documents are in the documents folder?"

**`upload_file(local_path: str, folder_alias: str, filename: Optional[str])`**
- Purpose: Upload a local file
- Returns: File ID and confirmation
- Access control: Only to configured folders
- Agent use: "Save this report to the documents folder"

**`get_file_content(file_id: str, folder_alias: str)`**
- Purpose: Download a file
- Returns: Local path to downloaded file
- Access control: Validated against folder
- Agent use: "Download the report so I can analyze it"

**`delete_file(file_id: str, folder_alias: str)`**
- Purpose: Remove a file
- Returns: Success/error status
- Access control: Only within configured folders
- Agent use: "Remove this old file"

### Design Patterns for Agent Effectiveness

#### 1. Alias-Based Access

```python
@mcp.tool()
def list_sheets(sheet_alias: str) -> list[str]:
    """Lists all sheets (tabs) in a given spreadsheet identified by its alias."""
```

**Why aliases?**
- Agents work with familiar names (e.g., "prompts") not IDs
- Configuration prevents ID leakage
- Aliases provide semantic meaning to agents

#### 2. Structured Return Values

```python
return {
    "status": "success",
    "prompts": [
        {
            "Name": "prompt_name",
            "Content": "...",
            "Created By": "user",
            "Created At": "2025-01-27T...",
            ...
        },
        ...
    ]
}
```

**Why structured?**
- Agents can parse and act on specific fields
- Consistent across all tools (status + data)
- Error status makes failure clear

#### 3. Safe Defaults

```python
@mcp.tool()
def get_sheet_status(sheet_alias: str, range_name: str = "README!A1") -> dict:
```

**Why default range?**
- README tab provides table of contents
- Agents get useful info without knowing exact range
- Agents can override if they need specific data

#### 4. Error Messages for Agents

```python
try:
    service, spreadsheet_id = get_sheets_service(sheet_alias)
    return service.list_sheet_titles(spreadsheet_id)
except Exception as e:
    return [f"Error: {str(e)}"]  # Agent sees error
```

**Why important?**
- Agents can diagnose issues (bad alias, auth failed, etc.)
- Structured errors help agents retry or ask user
- Prevents silent failures

### Tool Safeguards

#### Resource Validation

```python
def get_sheet_resource(self, alias: str) -> ResourceConfig:
    if alias in self.config.sheets:
        return self.config.sheets[alias]
    raise ValueError(f"Access Denied: Sheet alias '{alias}' not found")
```

**Prevents:**
- Agent accessing arbitrary spreadsheets
- Typos in aliases silently succeeding
- Cross-profile confusion

#### Scope Enforcement

```python
def _verify_access(self, parent_id: str):
    if parent_id not in self.allowed_folder_ids:
        raise PermissionError(f"Access to folder {parent_id} is not allowed.")
```

**Prevents:**
- Agent uploading to wrong folder
- Accidental Drive operations outside configured set
- Confused credential contexts

---

## Logging and Observability

### Logging Configuration

```python
import logging

VERBOSE = os.getenv('GOOGLE_PERSONAL_MCP_VERBOSE', '').lower() in ('1', 'true', 'yes')
logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.WARNING,
    format='[%(levelname)s] %(message)s',
    stream=sys.stderr  # Logs to stderr, not stdout (MCP uses stdout)
)
logger = logging.getLogger(__name__)
```

**Design:**
- Default: WARNING level (quiet for production)
- Controlled by `GOOGLE_PERSONAL_MCP_VERBOSE` environment variable
- Output to stderr (doesn't interfere with MCP stdout communication)

### Verbose Logging Points

**Authentication**:
```python
logger.info(f"Starting OAuth2 authentication for profile '{profile}'...")
logger.debug(f"Refreshing token for profile '{profile}'...")
logger.info(f"Authorization token saved to: {token_path}")
```

**Credential Loading**:
```python
logger.warning(f"Failed to load token from {token_path}: {e}")
logger.info(f"Token exists but lacks required scopes. Re-authenticating for profile '{profile}'...")
```

**API Operations**:
```python
logger.debug(f"Download {int(status.progress() * 100)}%.")
```

**Configuration**:
```python
logger.error(f"Failed to load config from {self.config_path}: {e}")
```

### Use Cases for Verbose Logging

**During Development:**
```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
google-personal sheets list-tabs prompts
```

**During Debugging:**
```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
google-personal-mcp  # MCP server with detailed logs to stderr
```

**In Client Configuration:**
```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "google-personal-mcp",
      "env": {
        "GOOGLE_PERSONAL_MCP_VERBOSE": "1"
      }
    }
  }
}
```

### Observability Recommendations (In Checklist)

1. **Structured logging**: Use JSON format for log aggregation
2. **Audit logging**: Track which operations were performed
3. **Performance monitoring**: Log API call duration
4. **Error tracking**: Central error logging service
5. **Metrics**: Tool call counts, latency histograms

---

## Best Practices and Patterns

### 1. Service Locator Pattern

```python
def get_sheets_service(alias: str) -> Tuple[SheetsService, str]:
    """Get service and resource ID from alias."""
    resource = config_manager.get_sheet_resource(alias)
    context = GoogleContext(profile=resource.profile)
    return SheetsService(context), resource.id
```

**Benefit:** Centralizes service instantiation. Tool layer doesn't know about ConfigManager.

### 2. Context Object Pattern

```python
class GoogleContext:
    def __init__(self, profile: str, scopes: Optional[List[str]] = None):
        self.credentials = self.auth_manager.get_credentials(profile, scopes)

    @property
    def sheets(self):
        return self.get_service("sheets", "v4")

    @property
    def drive(self):
        return self.get_service("drive", "v3")
```

**Benefit:** Lazy-loads services. Credentials fetched once, reused across tools in same context.

### 3. Lazy-Load Service Objects

```python
class GoogleContext:
    def __init__(self, ...):
        self._services = {}

    def get_service(self, service_name: str, version: str):
        key = (service_name, version)
        if key not in self._services:
            self._services[key] = build(service_name, version, ...)
        return self._services[key]
```

**Benefit:** Avoids building unused services. Multiple tools in same profile share service instance.

### 4. Access Control at Service Layer

```python
class DriveService:
    def __init__(self, context: GoogleContext, allowed_folder_ids: List[str]):
        self.allowed_folder_ids = allowed_folder_ids

    def _verify_access(self, parent_id: str):
        if parent_id not in self.allowed_folder_ids:
            raise PermissionError(...)
```

**Benefit:** All file operations validate against allowed list. Single point of enforcement.

### 5. Configuration Validation with Pydantic

```python
class ResourceConfig(BaseModel):
    id: str  # Type validated at load time
    profile: str = "default"
    description: Optional[str] = None

class AppConfig(BaseModel):
    sheets: Dict[str, ResourceConfig]  # Validates nested models
    drive_folders: Dict[str, ResourceConfig]
```

**Benefit:** Malformed config.json caught immediately on load, not at runtime during tool call.

### 6. Error Handling Strategy

**Tool layer catches all exceptions:**
```python
@mcp.tool()
def list_sheets(sheet_alias: str) -> dict:
    try:
        service, spreadsheet_id = get_sheets_service(sheet_alias)
        return {"status": "success", "sheets": ...}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**Benefit:** MCP server never crashes. Agents see clear error messages.

### 7. Environment-Driven Behavior

```python
VERBOSE = os.getenv('GOOGLE_PERSONAL_MCP_VERBOSE', '').lower() in ('1', 'true', 'yes')
logging.basicConfig(level=logging.DEBUG if VERBOSE else logging.WARNING, ...)

config_path = os.getenv('GOOGLE_PERSONAL_CREDENTIALS', default_path)
```

**Benefit:** Behavior controllable at deployment time without code changes.

### 8. Reusable Service Classes

```python
class SheetsService:
    def __init__(self, context: GoogleContext):
        self.context = context
        self.service = context.sheets

    # Methods: read_range, write_range, list_sheet_titles, etc.
```

**Benefit:** Same service class used by MCP tools, CLI commands, and standalone scripts. No duplication.

---

## Deployment Considerations

### Running as MCP Server

```bash
# For Gemini/Claude clients
google-personal-mcp

# Or with logging
export GOOGLE_PERSONAL_MCP_VERBOSE=1
google-personal-mcp
```

**Entry point:** `src/google_personal_mcp/server.py:main()`

### Running as CLI

```bash
# For manual operations
google-personal config list-sheets
google-personal drive list-files documents
google-personal sheets list-tabs prompts
```

**Entry point:** `src/google_mcp_core/cli.py:main()`

### Installation

```bash
pip install -e .  # Editable install from pyproject.toml
```

**Registers commands:**
- `google-personal-mcp`: MCP server entry point
- `google-personal`: CLI entry point

---

## Summary

This MCP server demonstrates:

✅ **Clean separation of concerns**: Service layer, authentication layer, MCP layer
✅ **Profile-based multi-account support**: Separate credentials and tokens per profile
✅ **Access control**: ConfigManager provides alias-based access, DriveService enforces folders
✅ **Security**: OAuth scopes, folder restrictions, credential storage isolation
✅ **Reusable code**: `google_mcp_core` shared between MCP server and CLI
✅ **Type safety**: Pydantic models, type hints, cyclopts validation
✅ **Observability**: Verbose logging with environment control
✅ **Error handling**: Graceful degradation, clear error messages
✅ **Testing**: Both unit and integration test patterns

The patterns and practices documented here should be applied to other MCP server projects for consistency and best practices across the MCP server ecosystem.

---
Last Updated: 2026-01-28
