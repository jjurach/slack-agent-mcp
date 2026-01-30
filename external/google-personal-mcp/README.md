# Google Sheets MCP Server

This subproject implements a Managed Code Project (MCP) server that interacts with Google Sheets to store and retrieve prompts and ideas. It allows MCP clients to manage textual content, including metadata like timestamps and authorship, across various sheets (tabs) in a specified Google Spreadsheet.

## Setup Instructions

1.  **Navigate to the project directory:**
    ```bash
    cd google-personal-mcp
    ```

2.  **Create and activate a virtual environment (if you haven't already):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -e ../external/fastmcp
    ```

## Google Sheets API Authentication

To allow the MCP server to interact with your Google Sheets, you need to set up Google Sheets API access and obtain `credentials.json`.

1.  **Enable the Google Sheets and Drive APIs:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Enabled APIs & Services".
    *   Search for "Google Sheets API" and enable it.
    *   Search for "Google Drive API" and enable it.

2.  **Create OAuth 2.0 Client IDs:**
    *   In the Google Cloud Console, go to "APIs & Services" > "Credentials".
    *   Click "CREATE CREDENTIALS" > "OAuth client ID".
    *   Choose "Desktop app" as the application type.
    *   Give it a name (e.g., "GoogleSheetsMCP").
    *   Click "CREATE".

3.  **Download the OAuth 2.0 credentials:**
    *   After creating the client ID, a dialog will appear with your client ID and client secret.
    *   Click "DOWNLOAD JSON" to save the credentials file.
    *   **Rename the downloaded file to `credentials.json`** and place it in your profile directory (see below).

## Credential Storage (Profile-Based)

The server stores OAuth credentials and authorization tokens organized by profile. This allows you to manage multiple Google accounts or authentication scopes.

### Directory Structure

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

### Setting Up a Profile

For the default profile:

```bash
# Create the profile directory
mkdir -p ~/.config/google-personal-mcp/profiles/default

# Copy your downloaded credentials
mv ~/Downloads/credentials.json ~/.config/google-personal-mcp/profiles/default/
```

For alternative profiles:

```bash
# Create alternate profile directory
mkdir -p ~/.config/google-personal-mcp/profiles/work

# Add credentials for that profile
mv ~/Downloads/work_credentials.json ~/.config/google-personal-mcp/profiles/work/credentials.json
```

### How It Works

- **credentials.json**: Contains your OAuth 2.0 client ID and secret (downloaded from Google Cloud Console). This is the same file for all uses of that profile.
- **token.json**: Created automatically after first authentication. Contains your authorization token. Generated separately for each profile and set of scopes.

Both files are required for authentication. When you run the server for the first time with a profile, it will:
1. Look for `credentials.json` in the profile directory
2. If `token.json` doesn't exist or is invalid, open your browser for authentication
3. Save the authorization token to `token.json`

**Security Note:** Both `credentials.json` and `token.json` are sensitive files. They are added to `.gitignore` to prevent accidental commits.

## Resource Configuration

The server uses a `config.json` file to manage aliases for your Google Sheets and Drive folders. This allows you to reference resources by friendly names instead of long IDs.

### Configuration File Location

The server looks for `config.json` at:
```
~/.config/google-personal-mcp/config.json
```

### Configuration File Structure

Create a `config.json` file with aliases for your resources:

```json
{
  "sheets": {
    "prompts": {
      "id": "YOUR_SPREADSHEET_ID",
      "profile": "default",
      "description": "Main prompts storage"
    }
  },
  "drive_folders": {
    "documents": {
      "id": "YOUR_FOLDER_ID",
      "profile": "default",
      "description": "Personal documents"
    }
  }
}
```

### Field Reference

- **sheets**: Dictionary of spreadsheet aliases
- **drive_folders**: Dictionary of Drive folder aliases
- **id**: The Google resource ID (spreadsheet ID or folder ID)
- **profile**: Authentication profile to use (default: `"default"`)
- **description**: Optional human-readable description

### Finding Your Resource IDs

**Spreadsheet ID:**
- Open your spreadsheet in Google Sheets
- Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
- Copy the ID between `/d/` and `/edit`

**Folder ID:**
- Open your folder in Google Drive
- Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID`
- Copy the ID after `/folders/`

### Example Setup

```bash
# Create the config directory
mkdir -p ~/.config/google-personal-mcp

# Copy the example file
cp config.json.example ~/.config/google-personal-mcp/config.json

# Edit with your spreadsheet and folder IDs
nano ~/.config/google-personal-mcp/config.json
```

## Verbose Logging

Enable verbose logging to see detailed information about credential file search, authentication, and API operations:

```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=1
```

When verbose mode is enabled, the server will display:
- Which credential/token file location was used
- Authentication flow steps
- API operation details
- Debugging information for troubleshooting

To disable verbose logging:
```bash
export GOOGLE_PERSONAL_MCP_VERBOSE=0
# or simply unset the variable
unset GOOGLE_PERSONAL_MCP_VERBOSE
```

## Drive Tool & Diagnostics

The project includes a utility script `scripts/drive-tool.py` to help diagnose authentication issues and list files in your Google Drive. This tool is independent of the main MCP server but shares the same authentication profile (`default` by default).

**Usage:**
```bash
python3 scripts/drive-tool.py
```

**Features:**
*   **Lists all files:** It requests the `drive.readonly` scope to see *all* files in your Drive, not just those created by this app (unlike the main server which uses the restricted `drive.file` scope).
*   **Auto-Remediation:** If your current cached token (`token.json`) lacks the necessary permissions, the tool will automatically detect this and trigger a re-authentication flow. You will be prompted to visit a URL to authorize the broader scopes.
*   **Diagnostics:** Useful for verifying that your `credentials.json` is working and that the application can successfully talk to the Google Drive API. If this tool works but the server doesn't, the issue is likely in the server configuration or specific file restrictions.

## Running the MCP Server

The `fastmcp` server can be run directly.

1.  **Ensure your virtual environment is active:**
    ```bash
    source venv/bin/activate
    ```

2.  **Run the server:**
    ```bash
    python main.py
    ```
    The server will run in the foreground. You can stop it by pressing `Ctrl+C`.

The server will typically be accessible via a `fastmcp` client, which can then invoke the exposed tools.

## Configuring .gemini/settings.json

To use this MCP server with Gemini, add the following configuration to your `.gemini/settings.json` file:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "google-personal-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**With verbose logging enabled:**
```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "google-personal-mcp",
      "args": [],
      "env": {
        "GOOGLE_PERSONAL_MCP_VERBOSE": "1"
      }
    }
  }
}
```

**Notes:**
- Ensure the package is installed with `pip install -e .` so that the `google-personal-mcp` command is available in your PATH
- The `cwd` parameter is optional now - the server will automatically search for credentials in standard locations
- If you want to specify a custom credential location, use the `GOOGLE_PERSONAL_CREDENTIALS` environment variable in the `env` section

## Available Tools

The following tools are exposed by the `fastmcp` server:

*   **`list_sheets(spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> list[str]`**: Lists all sheets (tabs) in a given spreadsheet.
*   **`create_sheet(new_sheet_name: str, spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> dict`**: Creates a new sheet (tab) in a given spreadsheet.
*   **`get_sheet_status(spreadsheet_id: str = DEFAULT_SPREADSHEET_ID, range_name: str = "README!A1") -> dict`**: Gets the status of a sheet (reads data from a specified range).
*   **`insert_prompt(sheet_name: str, prompt_name: str, content: str, author: str = "Google Sheets MCP", spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> dict`**: Inserts a prompt into a sheet.
*   **`get_prompts(sheet_name: str, spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> dict`**: Gets all prompts from a sheet.
*   **`initialize_readme_sheet(spreadsheet_id: str = DEFAULT_SPREADSHEET_ID) -> dict`**: Initializes the "README" sheet with some default content.

These tools are designed to be invoked programmatically via a `fastmcp` client. For example, using a `fastmcp` client library in Python, you might call `client.tools.list_sheets()`.

## Command-Line Interface

The `google-personal` CLI provides tools for managing Google Drive files, Sheets, and configuration.

### Drive Commands

#### List All Files (Diagnostic)

List all files accessible by the current credentials:

```bash
google-personal drive list-all-files [--profile <profile>]
```

**Options:**
- `--profile`: Authentication profile (default: "default")

#### List Files in Folder

List files in a specific Drive folder:

```bash
google-personal drive list-files [--folder <folder>] [--profile <profile>]
```

**Options:**
- `--folder`: Folder alias (optional if only one folder configured)
- `--profile`: Authentication profile (default: "default")

**Example:**
```bash
google-personal drive list-files --folder documents
```

#### Download File

Download a file from Drive by name:

```bash
google-personal drive get-file --remote-file <filename> [--local-file <path>] [--folder <folder>] [--profile <profile>]
```

**Options:**
- `--remote-file`: Name of the file in Drive (required)
- `--local-file`: Local path to save (optional, defaults to basename of remote file)
- `--folder`: Folder alias (optional if only one folder configured)
- `--profile`: Authentication profile (default: "default")

**Examples:**
```bash
# Download with auto-detected filename
google-personal drive get-file --remote-file 'Recording 3.acc'

# Download with custom local name
google-personal drive get-file --remote-file 'Report.pdf' --local-file 'Q4-Report.pdf' --folder documents
```

**Safety:** Command fails if local file already exists to prevent accidental overwrites.

#### Upload File

Upload a file to Drive:

```bash
google-personal drive put-file --local-file <path> [--remote-file <filename>] [--folder <folder>] [--profile <profile>]
```

**Options:**
- `--local-file`: Local file to upload (required)
- `--remote-file`: Name for the file in Drive (optional, defaults to basename of local file)
- `--folder`: Folder alias (optional if only one folder configured)
- `--profile`: Authentication profile (default: "default")

**Examples:**
```bash
# Upload with same name
google-personal drive put-file --local-file report.pdf

# Upload with custom name
google-personal drive put-file --local-file ./docs/report.pdf --remote-file 'Q4-Report.pdf' --folder documents
```

#### Remove File

Remove a file from Drive by name:

```bash
google-personal drive remove-file --remote-file <filename> [--folder <folder>] [--profile <profile>]
```

**Options:**
- `--remote-file`: Name of the file to remove (required)
- `--folder`: Folder alias (optional if only one folder configured)
- `--profile`: Authentication profile (default: "default")

**Example:**
```bash
google-personal drive remove-file --remote-file 'old-backup.zip' --folder documents
```

### Configuration Commands

#### List Configured Sheets

```bash
google-personal config list-sheets [--profile <profile>]
```

#### List Configured Folders

```bash
google-personal config list-folders [--profile <profile>]
```

### Sheets Commands

See the Available Tools section above for MCP tools. The CLI also provides direct access to sheets operations:

```bash
google-personal sheets list-tabs --sheet-alias <alias> [--profile <profile>]
google-personal sheets get-status --sheet-alias <alias> [--range-name <range>] [--profile <profile>]
google-personal sheets get-prompts --sheet-alias <alias> --sheet-tab-name <tab> [--profile <profile>]
google-personal sheets insert-prompt --sheet-alias <alias> --sheet-tab-name <tab> --prompt-name <name> --content <content> [--author <author>] [--profile <profile>]
```

## MCP Server Verification

### Simple Verification Test

For quick verification that your MCP server is working correctly, use this simple test prompt:

**Simple Test Prompt:**
```
Use the Google Sheets MCP tool to list all prompts from the 'Gemini Prompts' sheet. Just show me the raw data exactly as returned by the tool.
```

**Why this works for verification:**
- This prompt forces the AI to use the `get_prompts` tool
- You can easily verify by checking if the AI returns actual prompt data from your sheet
- No complex summarization required - just raw tool output
- Clear success indicator: if you see actual prompt names/content from your sheet, the MCP connection is working

**Quick Verification Steps:**
1. Add a test prompt to the "Gemini Prompts" sheet using the `insert_prompt` tool (e.g., name: "Test Prompt", content: "This is a test")
2. Send the simple test prompt above to Gemini/Claude
3. Verify the AI shows your actual test prompt data (not generic responses)
4. Success = MCP server is connected and working

### Advanced Test Prompt

For comprehensive testing, use this prompt which requires the AI to summarize sheet content:

**Advanced Test Prompt:**
```
Use the Google Sheets MCP tool to get all prompts from the 'Gemini Prompts' sheet and provide a comprehensive summary of their content, including key themes and any notable patterns you observe.
```

**Expected Behavior:**
- The AI should successfully call the `get_prompts` tool on the "Gemini Prompts" sheet
- If the sheet exists and contains prompts, the AI will receive the prompt data and generate a summary
- If the sheet is empty or doesn't exist, the AI should report this clearly
- The MCP server connection is working if the AI can access the tool and retrieve data (or report appropriate errors)

**Prerequisites:**
- Ensure the "Gemini Prompts" sheet exists in your spreadsheet (create it if needed using the `create_sheet` tool)
- Add some test prompts to the sheet using the `insert_prompt` tool for meaningful verification
- Confirm your MCP client (Gemini/Claude) is configured to use this server

**Verification Steps:**
1. Send the test prompt above to your AI assistant
2. Check that it attempts to use the Google Sheets MCP tools (you may see tool call indicators in the interface)
3. Verify the AI provides a summary based on actual sheet data rather than generic responses
4. If the AI cannot access the tools, check your MCP server configuration and authentication

## Summarization Test Prompt

For easy verification that the MCP server is working correctly with summarization capabilities:

**Test Prompt:**
```
Please use the Google Sheets MCP tool to retrieve all prompts from the 'Gemini Prompts' sheet and provide a detailed summary of their content, including the total number of prompts, key themes, and any patterns you notice in the prompt names or content.
```

**Why this works for verification:**
- Forces the AI to call the `get_prompts` tool on the "Gemini Prompts" sheet
- Requires actual data processing (counting, summarizing, pattern recognition)
- Easy to verify: if you see specific details from your actual sheet data, the MCP connection works
- Clear failure indicator: if the AI gives generic responses instead of your actual data, the server isn't connected

**Quick Verification Steps:**
1. Ensure the "Gemini Prompts" sheet exists and contains at least 2-3 test prompts
2. Send the test prompt above to Gemini/Claude
3. Check that the AI response includes:
   - Actual prompt names/content from your sheet (not generic examples)
   - A specific count of prompts (e.g., "There are 5 prompts in total")
   - Real themes/patterns from your actual data
4. Success = MCP server is connected and functioning correctly

**Prerequisites:**
- "Gemini Prompts" sheet exists in your spreadsheet
- Sheet contains some test prompts (use `insert_prompt` tool to add them if needed)
- MCP client properly configured to use this server

## Connecting to MCP Clients

This MCP server can be connected to any MCP-compatible client that supports the MCP protocol. The server exposes tools for programmatic Google Sheets access, allowing clients to manage spreadsheet content, store prompts, and retrieve data across multiple sheets.

## Documentation

### For AI Agents
- **[Mandatory Reading](docs/mandatory.md)** - MUST READ FIRST before every session
- **[AGENTS.md](AGENTS.md)** - Mandatory workflow for AI agents working on this project
- **[Definition of Done](docs/definition-of-done.md)** - Quality standards and checklists
- **[Workflows](docs/workflows.md)** - Development workflows for MCP tools and Google API integration
- **[CLAUDE.md](CLAUDE.md)** - Instructions for Claude Code users

### For Developers
- **[Documentation Index](docs/README.md)** - Complete documentation navigation
- **[Architecture](docs/architecture.md)** - System architecture and design
- **[Implementation Reference](docs/implementation-reference.md)** - Code patterns and templates
- **[Contributing](docs/contributing.md)** - Contribution guidelines

### Examples
- **[MCP Tool Example](docs/examples/mcp-tool-example.md)** - Complete MCP tool walkthrough
- **[Google API Integration Example](docs/examples/google-api-integration.md)** - API integration walkthrough
- **[Claude Code Examples](docs/examples/claude-code-examples.md)** - Project-specific examples

### Guides
- **[MCP Development Guide](docs/mcp-development-guide.md)** - Development and debugging
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions