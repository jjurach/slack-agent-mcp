# Troubleshooting Guide

Common issues and solutions for the Google Personal MCP Server.

## Authentication Issues

### "credentials.json not found for profile 'default'"

**Problem:** Server can't find your OAuth credentials file.

**Solution:**

1. Check the file exists:
   ```bash
   ls -la ~/.config/google-personal-mcp/profiles/default/credentials.json
   ```

2. If not found, download from Google Cloud Console:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - API & Services > Credentials
   - Select your OAuth 2.0 Client ID
   - Click the download icon (⬇️) or "Download JSON"
   - Save as `credentials.json` in the correct directory

3. Create the directory if needed:
   ```bash
   mkdir -p ~/.config/google-personal-mcp/profiles/default
   ```

### "Token expired or invalid scopes"

**Problem:** Token is expired or doesn't have required permissions.

**Solution:**

1. The server will automatically re-authenticate on next use
2. You'll be prompted to visit a URL to authorize
3. If you want to force immediate re-auth, delete the token:
   ```bash
   rm ~/.config/google-personal-mcp/profiles/default/token.json
   ```

### "OAuth2 authentication failed"

**Problem:** OAuth flow couldn't complete.

**Solution:**

1. Check internet connectivity
2. Verify credentials.json is valid JSON:
   ```bash
   python -c "import json; json.load(open('~/.config/google-personal-mcp/profiles/default/credentials.json'))"
   ```
3. Check that OAuth app is not restricted:
   - Verify "Authorized JavaScript origins" includes `http://localhost`
   - Verify "Authorized redirect URIs" includes appropriate ports
4. Enable verbose logging to see details:
   ```bash
   export GOOGLE_PERSONAL_MCP_VERBOSE=1
   google-personal-mcp
   ```

## Configuration Issues

### "Sheet alias 'prompts' not found in configuration"

**Problem:** Config doesn't have the sheet you're trying to access.

**Solution:**

1. Check config file exists:
   ```bash
   cat ~/.config/google-personal-mcp/config.json
   ```

2. If not found, create it:
   ```bash
   mkdir -p ~/.config/google-personal-mcp
   cat > ~/.config/google-personal-mcp/config.json << 'EOF'
   {
     "sheets": {
       "prompts": {
         "id": "YOUR_SPREADSHEET_ID",
         "profile": "default",
         "description": "Main prompts storage"
       }
     },
     "drive_folders": {}
   }
   EOF
   ```

3. Add your spreadsheet ID:
   - Open your sheet in Google Sheets
   - The URL is: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the ID and replace `YOUR_SPREADSHEET_ID` above

4. Verify JSON syntax:
   ```bash
   python -m json.tool ~/.config/google-personal-mcp/config.json
   ```

### "Invalid JSON in config file"

**Problem:** Configuration file has JSON syntax errors.

**Solution:**

1. Validate the JSON:
   ```bash
   python -m json.tool ~/.config/google-personal-mcp/config.json
   ```

2. Fix syntax errors (common mistakes):
   - Missing commas between properties
   - Trailing commas in arrays/objects
   - Unquoted keys or values
   - Invalid escape sequences

3. If you're unsure, start from the example:
   ```bash
   cp README.md  # Extract example from README
   ```

## API Permission Issues

### "Access denied" when trying to access a folder

**Problem:** Server doesn't have permission to access the folder.

**Solution:**

1. Check your configuration lists the folder:
   ```bash
   cat ~/.config/google-personal-mcp/config.json | grep -A5 "drive_folders"
   ```

2. Verify the folder is shared with your Google account
3. Check the scope is "drive" or "drive.file":
   - The server uses `drive.file` scope by default (only app-created files)
   - To access all Drive files, use the CLI tool: `google-personal drive list-all-files`

### "Files not appearing in folder listing"

**Problem:** Uploaded files don't show up when listing.

**Solution:**

1. Check file wasn't deleted:
   ```bash
   google-personal drive list-files YOUR_FOLDER_ALIAS
   ```

2. If still not showing:
   - Try uploading a test file via Drive UI
   - Check folder isn't archived or in Trash
3. Note: Files created outside the app may not appear if using `drive.file` scope
   - Use `google-personal drive list-all-files` to see all files

## Server Startup Issues

### "Server fails to start silently"

**Problem:** MCP server exits without clear error message.

**Solution:**

1. Run with verbose logging:
   ```bash
   export GOOGLE_PERSONAL_MCP_VERBOSE=1
   google-personal-mcp
   ```

2. Check stderr for errors:
   ```bash
   google-personal-mcp 2>&1 | head -20
   ```

3. Check if port is in use (if applicable):
   ```bash
   lsof -i :8000  # Or whatever port your client uses
   ```

4. Verify dependencies are installed:
   ```bash
   python -c "import mcp; import google.auth"
   ```

### "Import errors when starting server"

**Problem:** Python can't find required modules.

**Solution:**

1. Check virtual environment is activated:
   ```bash
   which python  # Should show venv path
   ```

2. Reinstall in development mode:
   ```bash
   pip install -e .
   ```

3. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

## Logging & Debugging

### Enable Structured JSON Logging

```bash
export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
google-personal-mcp
```

Then parse logs with jq:
```bash
google-personal-mcp 2>&1 | jq '.message'
```

### Enable Debug Mode

Disables credential masking (use only for debugging!):
```bash
export GOOGLE_PERSONAL_MCP_DEBUG=1
google-personal-mcp
```

### Check Audit Log

```bash
# View recent audit entries
tail -n 20 ~/.config/google-personal-mcp/audit.log

# Parse as JSON
tail -f ~/.config/google-personal-mcp/audit.log | jq .
```

### Test Specific Tool

```python
from google_personal_mcp.server import list_configured_sheets
result = list_configured_sheets()
print(result)
```

## Performance Issues

### "Slow API responses"

**Problem:** Tools taking longer than expected.

**Solution:**

1. Check network connectivity:
   ```bash
   ping google.com
   ```

2. Check API quota usage:
   - Google Cloud Console > APIs & Services > Quota
   - Look for "Sheets API" and "Drive API"
   - If near limit, wait before retrying

3. Enable timing logs (add to code):
   ```python
   import time
   start = time.time()
   result = service.list_sheet_titles(...)
   print(f"Took {time.time() - start:.2f}s")
   ```

### "Out of memory"

**Problem:** Server uses too much memory.

**Solution:**

1. Check for large file downloads (they're buffered in memory)
   - Currently files are downloaded fully before returning
   - Streaming is a future enhancement

2. Restart the server:
   ```bash
   kill <PID>
   google-personal-mcp
   ```

3. Reduce frequency of large operations

## Getting Help

If your issue isn't covered here:

1. **Check the logs** with verbose mode enabled
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Python version: `python --version`
   - Error message and traceback
   - Steps to reproduce
   - Relevant config (remove sensitive IDs)

4. **Enable debug logging** for more details:
   ```bash
   export GOOGLE_PERSONAL_MCP_VERBOSE=1
   export GOOGLE_PERSONAL_MCP_DEBUG=1
   export GOOGLE_PERSONAL_MCP_JSON_LOGS=1
   google-personal-mcp 2>&1 | head -100
   ```

## Known Limitations

- Large files (>100MB) may be slow to upload/download
- Retry logic uses default exponential backoff (not configurable yet)
- No caching of sheet metadata (each tool call fetches fresh)
- Drive API limited to `drive.file` scope by default

See `docs/todo.md` for planned enhancements.
