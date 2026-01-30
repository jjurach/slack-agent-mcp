# Claude Code Examples - MCP Development

Quick reference examples for using Claude Code with the Google Personal MCP Server project.

For complete Claude Code documentation, see [system-prompts/tools/claude-code.md](../system-prompts/tools/claude-code.md).

## Quick Start

```bash
cd /home/phaedrus/AiSpace/google-personal-mcp
claude-code
```

## Example 1: Adding a New MCP Tool

```
> Add a new MCP tool to list Drive files in a folder.
>
> Requirements:
> - Tool name: list_drive_files
> - Parameter: folder_alias (string)
> - Use DriveService
> - Follow standard tool template pattern
> - Include audit logging and credential masking
> - Write unit tests with mocked Drive API

Claude will:
1. Read existing tools in server.py for pattern
2. Check if DriveService has list_files method
3. Implement or enhance DriveService method
4. Add MCP tool following standard template
5. Write unit tests with mock_drive_service fixture
6. Run tests to verify
7. Update documentation
```

## Example 2: Debugging a Test Failure

```
> pytest tests/test_sheets_service.py::test_read_cells -v
> (test fails)
>
> Debug this test failure

Claude will:
1. Read the failing test to understand what it expects
2. Read the implementation being tested
3. Identify the mismatch (e.g., mock not configured correctly)
4. Fix the issue
5. Re-run the test to verify
6. Check related tests to ensure no regressions
```

## Example 3: Understanding OAuth Flow

```
> Explain how OAuth authentication works in this project.
> Include the flow from credentials.json to making API calls.

Claude will:
1. Read auth.py to understand AuthManager
2. Read context.py to see how credentials are used
3. Trace the flow:
   - credentials.json → InstalledAppFlow → browser auth
   - token.json saved with refresh token
   - GoogleContext lazy-loads credentials
   - Automatic token refresh when expired
4. Explain profile-based credential storage
5. Show code examples at each step
```

## Example 4: Checking Credential Masking

```
> Verify that all error paths properly mask credentials.
> Check for any potential credential leaks.

Claude will:
1. Grep for mask_credentials() usage
2. Check each tool's error handling
3. Review utils/sanitizer.py patterns
4. Test with sample errors containing credentials
5. Identify any gaps in coverage
6. Suggest fixes if needed
```

## Example 5: Adding Google API Integration

```
> Add support for Google Calendar API.
>
> Requirements:
> - OAuth scope: calendar.readonly
> - Service class: CalendarService
> - Methods: list_events, get_event
> - Follow GoogleContext pattern
> - Add MCP tools for calendar operations

Claude will:
1. Update SCOPES in auth.py
2. Create src/google_mcp_core/calendar.py with CalendarService
3. Implement service locator: get_calendar_service()
4. Add MCP tools in server.py
5. Write unit tests with mocked Calendar API
6. Update documentation
7. Add re-authentication instructions to README
```

## Common Patterns

### Check Test Coverage

```
> Run tests with coverage report and identify untested code paths

Claude will:
1. Run: pytest tests/ --cov=src/google_mcp_core --cov-report=term-missing
2. Analyze coverage report
3. Identify critical untested code
4. Suggest tests to add
```

### Format and Lint Code

```
> Format all code and fix linting issues

Claude will:
1. Run: black src/ tests/
2. Run: ruff check --fix src/ tests/
3. Run: mypy src/
4. Fix remaining issues that can't be auto-fixed
5. Re-run checks to verify
```

### Verify No Credential Leaks

```
> Check the current changes for any credential leaks

Claude will:
1. Run: git diff
2. Search for patterns: credentials, token, api_key, ya29, etc.
3. Check for hardcoded IDs
4. Verify .gitignore is correct
5. Report findings
```

## Project-Specific File Locations

When asking Claude to work on specific components:

- **MCP Server & Tools**: `src/google_personal_mcp/server.py`
- **Service Layer**: `src/google_mcp_core/{sheets,drive,auth,config,context}.py`
- **Utilities**: `src/google_mcp_core/utils/{retry,sanitizer,context}.py`
- **Tests**: `tests/` (mirrors `src/` structure)
- **Configuration**: `~/.config/google-personal-mcp/config.json`
- **Credentials**: `~/.config/google-personal-mcp/profiles/{profile}/credentials.json`

## See Also

- [Claude Code Documentation](../system-prompts/tools/claude-code.md) - Complete guide
- [Implementation Reference](../implementation-reference.md) - Code patterns and templates
- [Workflows](../workflows.md) - Development workflows
- [Definition of Done](../definition-of-done.md) - Quality checklist

---
Last Updated: 2026-01-27
