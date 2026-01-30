# Spec: Drive File Operations Enhancement

**Date:** 2026-01-27
**Status:** Completed
**Completed:** 2026-01-28 00:20:50
**Workflow:** @logs-first
**Project Plan:** `dev_notes/project_plans/2026-01-27_23-53-21_plan-drive-file-operations.md`
**Change Documentation:** `dev_notes/changes/2026-01-28_00-20-50_drive-file-operations.md`

## User Request

- Fix the `google-personal drive list-all-files` command that isn't working
- Add new drive commands for file operations:
  - `list-files [--folder <folder>]` - List files in a folder
  - `get-file [--folder <folder>] --remote-file <filename> [--local-file <filename>]` - Download a file
  - `put-file [--folder <folder>] --local-file <filename> [--remote-file <filename>]` - Upload a file
  - `remove-file [--folder <folder>] --remote-file <filename>` - Remove a file
- Update README.md and CLI usage documentation

## Current State

### Existing Implementation

**Service Layer (`src/google_mcp_core/drive.py`):**
- `list_files(folder_id)` - Lists files in a specific folder (working)
- `list_all_files(pageSize)` - Lists all accessible files (broken)
- `download_file(file_id, local_path)` - Downloads by file ID (working)
- `upload_file(local_path, folder_id, filename)` - Uploads a file (working)
- `remove_file(file_id)` - Removes a file by ID (working)

**CLI Layer (`src/google_mcp_core/cli.py`):**
- `drive list-all-files [--profile]` - Exists at line 72-104 (broken - missing allowed_folder_ids)
- `drive list-files <folder_alias> [--profile]` - Exists at line 106-132 (working)
- No commands for get-file, put-file, or remove-file by name

### Problems Identified

1. **list-all-files broken:** Line 85 creates `DriveService(context)` without passing `allowed_folder_ids=[]`, which may cause issues when DriveService expects it
2. **Missing CLI commands:** No wrapper commands that work with file names instead of IDs
3. **Documentation outdated:** README doesn't document the drive commands

## Goals

1. Fix the `list-all-files` command to work correctly
2. Add CLI commands that work with file names and folder aliases
3. Support optional folder aliases (default to single folder when only one is configured)
4. Support optional profile (default to "default" when only one profile exists)
5. Implement sensible defaults (e.g., derive local filename from remote file)
6. Add safety checks (e.g., fail if local file already exists on download)
7. Update documentation with all drive commands

## Scope

### Included

- Fix `drive list-all-files` command
- Add `drive get-file` command with file-by-name support
- Add `drive put-file` command with file-by-name support
- Add `drive remove-file` command with file-by-name support
- Update README.md with drive command documentation
- Add helper methods to DriveService if needed (e.g., find_file_by_name)

### Excluded

- Recursive folder operations
- Bulk file operations
- File pattern matching (wildcards)
- Progress bars for uploads/downloads
- Retry logic for failed operations

### Related

- May need to update `docs/workflows.md` if CLI patterns change
- May affect `docs/implementation-reference.md` if new patterns introduced

## Acceptance Criteria

- [ ] `google-personal drive list-all-files [--profile]` works correctly
- [ ] `google-personal drive list-files [--folder]` lists files in a folder
- [ ] `google-personal drive get-file --remote-file <name> [--local-file] [--folder]` downloads file by name
- [ ] `google-personal drive put-file --local-file <path> [--remote-file] [--folder]` uploads file
- [ ] `google-personal drive remove-file --remote-file <name> [--folder]` removes file by name
- [ ] --folder is optional when only one folder is configured
- [ ] --profile is optional when only one profile exists
- [ ] get-file derives local filename from remote file if not specified
- [ ] get-file fails if local file already exists (safety check)
- [ ] All commands have proper error handling and helpful error messages
- [ ] README.md documents all drive commands with examples
- [ ] All existing tests still pass
- [ ] Documentation is updated

## Technical Constraints

- Must follow existing CLI patterns (using cyclopts)
- Must use ConfigManager for resource lookups
- Must respect allowed_folder_ids for security
- Must follow project code style and patterns
- Must not break existing MCP tools

## Notes

The user's prompt specifies the exact command syntax expected:

```bash
google-personal drive list-all-files [--profile <profile>]
google-personal drive list-files [--folder <folder>]
google-personal drive get-file [--folder <folder>] --remote-file <filename> [--local-file <filename>]
google-personal drive put-file [--folder <folder>] --local-file <filename> [--remote-file <filename>]
google-personal drive remove-file [--folder <folder>] --remote-file <filename>
```

Key design notes:
- For `get-file`: If `--local-file` is omitted, derive from basename of `--remote-file`
- For `get-file`: Fail if local file exists (safety first)
- For `put-file`: If `--remote-file` is omitted, derive from basename of `--local-file`
- Optional `--folder` when only one folder configured (use that single folder)
- Optional `--profile` when only one profile exists (use default profile)
