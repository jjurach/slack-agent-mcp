# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-27

### Added
- Rename project from `google-sheets-mcp` to `google-personal-mcp`
- Multi-profile credential management system
- Enhanced credential file search in multiple locations
- Verbose logging support via `GOOGLE_MCP_VERBOSE` environment variable
- Google Drive integration with folder access management
- Drive diagnostics and inspection tools
- Configuration manager for resource aliases
- Integration tests for server validation
- Validation guide and authentication examples

### Changed
- Standardized project structure across all modules
- Updated all internal references to reflect new project name
- Environment variable names (`GOOGLE_PERSONAL_*` instead of `GOOGLE_SHEETS_*`)
- Configuration directory paths (`~/.config/google-personal-mcp` instead of `~/.google-sheets-mcp`)
- Improved authentication and credential handling

### Fixed
- Credential file path resolution in headless environments
- OAuth2 flow for console-based authentication
- Spreadsheet ID validation and error handling

## [0.1.0] - 2024-12-20

### Added
- Initial MCP server implementation for Google Sheets
- OAuth2 authentication flow
- Core tools: list_sheets, create_sheet, get_sheet_status
- Prompt management tools: insert_prompt, get_prompts
- Sheet initialization utilities
- Basic documentation and setup guides
- Test suite with pytest configuration
