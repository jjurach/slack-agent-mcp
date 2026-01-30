# Google Sheets MCP Server - Validation Guide

This guide explains how to validate that your MCP server is working correctly.

## Prerequisites

1. OAuth 2.0 credentials from Google Cloud Console (see setup below)
2. Virtual environment with dependencies installed
3. Profile directory created in `~/.config/google-personal-mcp/profiles/`

## Step 1: Authenticate with Google

Since this is running in a headless environment, use the console authentication script:

```bash
source venv/bin/activate
python authenticate_console.py
```

This will:
1. Display a URL for you to open in a browser
2. Ask you to complete authentication in the browser
3. Prompt you to paste the authorization code
4. Save the credentials to `token.json`
5. Test the connection to your Google Spreadsheet

## Step 2: Validate the MCP Server

After authentication, run the validation script:

```bash
source venv/bin/activate
python validate_server.py
```

This script will:
- Connect to the MCP server via stdio (like a real MCP client)
- List all available tools
- Verify all expected tools are present
- Test calling the `list_sheets` and `get_sheet_status` tools
- Confirm the server is working correctly

Expected output:
```
🔍 Starting MCP Server Validation...
✓ Server connection initialized
✓ Found 6 tools
✓ All expected tools are present
✓ list_sheets succeeded
✓ get_sheet_status succeeded
✅ Validation completed successfully!
```

## Step 3: Run Integration Tests (Optional)

Run the pytest integration tests:

```bash
source venv/bin/activate
pytest tests/test_server_integration.py -v
```

These tests will:
- Initialize an MCP client session
- Test server initialization
- Verify all tools are available
- Test tool execution
- Validate tool schemas

## Files Created

Three validation/testing files have been created:

1. **`authenticate_console.py`** - Console-based OAuth authentication (no browser required on server)
2. **`validate_server.py`** - Standalone validation script that connects as an MCP client
3. **`tests/test_server_integration.py`** - pytest integration tests

## Setting Up Credentials

Before validation, set up your OAuth credentials:

```bash
# Create the default profile directory
mkdir -p ~/.config/google-personal-mcp/profiles/default

# Download your credentials from Google Cloud Console, then:
mv ~/Downloads/credentials.json ~/.config/google-personal-mcp/profiles/default/
```

See the [README](../README.md) for complete credential setup instructions.

## Configuration for MCP Client

Add this to `$HOME/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "/home/myuser/google-personal-mcp/venv/bin/google-personal-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Note**: The server looks for credentials and configuration in `~/.config/google-personal-mcp/`, so no `cwd` parameter is needed.

## Available MCP Tools

Once authenticated and validated, your MCP server exposes these tools:

- **`list_sheets(spreadsheet_id)`** - Lists all sheets in a spreadsheet
- **`create_sheet(new_sheet_name, spreadsheet_id)`** - Creates a new sheet
- **`get_sheet_status(spreadsheet_id, range_name)`** - Gets sheet status
- **`insert_prompt(sheet_name, prompt_name, content, author, spreadsheet_id)`** - Inserts a prompt
- **`get_prompts(sheet_name, spreadsheet_id)`** - Retrieves all prompts from a sheet
- **`initialize_readme_sheet(spreadsheet_id)`** - Initializes the README sheet

## Troubleshooting

### "credentials.json not found"
- Ensure `credentials.json` is in `~/.config/google-personal-mcp/profiles/default/`
- Download it from Google Cloud Console > APIs & Services > Credentials > Your OAuth Client ID
- See "Credential Storage (Profile-Based)" section in [README.md](../README.md) for setup instructions

### "token.json is invalid"
- Delete the invalid token: `rm ~/.config/google-personal-mcp/profiles/default/token.json`
- The server will automatically regenerate it on next authentication
- You'll be prompted to authorize the app in your browser

### "could not locate runnable browser"
- This is expected in headless/SSH environments
- The server will provide a URL to visit manually on another device
- Copy the authorization code and paste it into the terminal

### Permission errors when accessing spreadsheet
- Ensure the Google account you authenticated with has access to the spreadsheet
- Check that the Google Sheets API is enabled in your Google Cloud project
- Verify the `config.json` has the correct spreadsheet ID for your profile
