# Google Sheets MCP Server

The Google Sheets MCP Server is a Managed Code Project (MCP) server that provides programmatic access to Google Sheets for storing and retrieving prompts, ideas, and other textual content with metadata.

## Purpose

This server enables MCP-compatible clients (such as AI assistants and automation tools) to:

- Create and manage Google Sheets programmatically
- Store prompts and ideas with timestamps and authorship metadata
- Organize content across multiple named sheets (tabs)
- Retrieve stored content for analysis or further processing

## Key Features

- **OAuth2 Authentication**: Secure access to Google Sheets API
- **Multi-sheet Support**: Organize content across different sheets/tabs
- **Metadata Tracking**: Automatic timestamps and author attribution
- **MCP Protocol**: Standard interface for MCP-compatible clients
- **Insert-at-top**: New entries automatically appear at the top for easy discovery

## Architecture

The server consists of:

- **Authentication module**: Handles Google API credentials and OAuth2 flow
- **Sheets utilities**: Core functions for reading/writing sheet data
- **MCP tools**: Exposed functions for clients to use
- **Data management**: Inserts new rows at the top with metadata

## Usage

1. Download OAuth 2.0 credentials from Google Cloud Console
2. Place `credentials.json` in `~/.config/google-personal-mcp/profiles/default/`
3. Configure resource aliases in `~/.config/google-personal-mcp/config.json`
4. Run the MCP server: `python src/google_personal_mcp/server.py`
5. Connect MCP-compatible clients to access the provided tools

See the [README](../README.md) for detailed setup instructions.

## Tools Available

- `list_sheets()`: List all sheets in a spreadsheet
- `create_sheet()`: Create new sheets
- `insert_prompt()`: Store prompts with metadata
- `get_prompts()`: Retrieve stored prompts
- `initialize_readme_sheet()`: Set up documentation sheets

## Dependencies

- fastmcp: MCP protocol implementation
- google-api-python-client: Google Sheets API
- google-auth-oauthlib: OAuth2 authentication
- google-auth: Authentication handling