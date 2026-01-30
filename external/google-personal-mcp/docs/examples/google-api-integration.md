# Example: Integrating a New Google API

This document provides a complete walkthrough of integrating a new Google API into the Google Personal MCP Server.

## Scenario

Add support for Gmail API to allow reading emails through MCP tools.

**Integration Requirements:**
- Google API: Gmail API v1
- OAuth Scope: `https://www.googleapis.com/auth/gmail.readonly`
- Service class: `GmailService`
- Methods: `list_messages()`, `get_message()`
- MCP tools: `list_gmail_messages`, `get_gmail_message`
- CLI commands: `gmail list`, `gmail get`

## Step 1: Update OAuth Scopes

**File:** `src/google_mcp_core/auth.py`

```python
# Add new scope to SCOPES list
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",  # NEW
]
```

**Important:** Users must re-authenticate when scopes change:

```bash
# Delete existing tokens to force re-authentication
rm ~/.config/google-personal-mcp/profiles/*/token.json
```

Document this in the commit message and README.

## Step 2: Create Service Class

**File:** `src/google_mcp_core/gmail.py` (new file)

```python
"""Gmail API service wrapper."""

from typing import List, Dict, Any, Optional
from google_mcp_core.context import GoogleContext
from google_mcp_core.utils.retry import retry_on_rate_limit


class GmailService:
    """
    Wrapper for Gmail API v1 operations.

    This service provides read-only access to Gmail messages through the
    Gmail API. All operations use the GoogleContext for authentication
    and service caching.

    Example:
        context = GoogleContext(profile="default")
        gmail = GmailService(context)
        messages = gmail.list_messages(query="from:example@gmail.com")
    """

    def __init__(self, context: GoogleContext):
        """
        Initialize Gmail service.

        Args:
            context: GoogleContext instance for authentication
        """
        self.context = context
        self.service = context.get_service("gmail", "v1")

    @retry_on_rate_limit(max_retries=3, backoff_base=2)
    def list_messages(
        self,
        query: str = "",
        max_results: int = 100,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List messages matching query.

        Args:
            query: Gmail search query (e.g., "from:user@example.com subject:test")
            max_results: Maximum number of messages to return (default: 100)
            label_ids: Filter by label IDs (e.g., ["INBOX", "UNREAD"])

        Returns:
            List of message metadata dictionaries with 'id' and 'threadId'

        Raises:
            HttpError: If API request fails

        Example:
            messages = service.list_messages(
                query="is:unread",
                max_results=50,
                label_ids=["INBOX"]
            )
        """
        request_params = {
            "userId": "me",
            "maxResults": max_results
        }

        if query:
            request_params["q"] = query

        if label_ids:
            request_params["labelIds"] = label_ids

        result = self.service.users().messages().list(**request_params).execute()

        return result.get("messages", [])

    @retry_on_rate_limit(max_retries=3, backoff_base=2)
    def get_message(
        self,
        message_id: str,
        format: str = "full"
    ) -> Dict[str, Any]:
        """
        Get full message by ID.

        Args:
            message_id: The ID of the message to retrieve
            format: Response format - "full", "metadata", "minimal", or "raw"
                   (default: "full")

        Returns:
            Full message dictionary including headers, body, and attachments

        Raises:
            HttpError: If API request fails or message not found

        Example:
            message = service.get_message(
                message_id="msg_123abc",
                format="full"
            )
            subject = next(
                h["value"] for h in message["payload"]["headers"]
                if h["name"].lower() == "subject"
            )
        """
        return self.service.users().messages().get(
            userId="me",
            id=message_id,
            format=format
        ).execute()

    def get_message_headers(self, message: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract headers from message as dict.

        Args:
            message: Message dictionary from get_message()

        Returns:
            Dictionary mapping header names to values (lowercase keys)

        Example:
            message = service.get_message("msg_123")
            headers = service.get_message_headers(message)
            print(f"From: {headers['from']}")
            print(f"Subject: {headers['subject']}")
        """
        headers = {}
        for header in message.get("payload", {}).get("headers", []):
            headers[header["name"].lower()] = header["value"]
        return headers
```

**Service design principles:**
- Uses `GoogleContext` for authentication (no credential management)
- API version explicitly specified: `get_service("gmail", "v1")`
- Retry logic with `@retry_on_rate_limit` decorator
- Comprehensive docstrings with examples
- Helper methods for common operations (e.g., `get_message_headers()`)
- Thin wrapper - returns raw or lightly processed API responses

## Step 3: Add Service Locator

**File:** `src/google_personal_mcp/server.py`

```python
from google_mcp_core.gmail import GmailService

def get_gmail_service(profile: str = "default") -> GmailService:
    """
    Get GmailService instance for profile.

    Args:
        profile: Authentication profile name

    Returns:
        Configured GmailService instance
    """
    context = GoogleContext(profile=profile)
    return GmailService(context)
```

## Step 4: Add MCP Tools

**File:** `src/google_personal_mcp/server.py`

```python
@mcp.tool()
def list_gmail_messages(query: str = "", max_results: int = 100, profile: str = "default") -> dict:
    """
    List Gmail messages matching search query.

    Args:
        query: Gmail search query (e.g., "from:user@example.com is:unread")
        max_results: Maximum number of messages to return (default: 100)
        profile: Authentication profile (default: "default")

    Returns:
        dict: Response with status, list of messages, and request_id
    """
    request_id = set_request_id()

    try:
        service = get_gmail_service(profile)
        messages = service.list_messages(query=query, max_results=max_results)

        audit_logger.log_tool_call(
            tool_name="list_gmail_messages",
            parameters={"query": query, "max_results": max_results},
            request_id=request_id,
            success=True
        )

        return {
            "status": "success",
            "result": {
                "messages": messages,
                "count": len(messages)
            },
            "request_id": request_id
        }

    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)

        audit_logger.log_tool_call(
            tool_name="list_gmail_messages",
            parameters={"query": query},
            request_id=request_id,
            success=False,
            error_message=error_msg
        )

        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id
        }

    finally:
        clear_request_id()


@mcp.tool()
def get_gmail_message(message_id: str, profile: str = "default") -> dict:
    """
    Get full Gmail message by ID.

    Args:
        message_id: ID of the message to retrieve
        profile: Authentication profile (default: "default")

    Returns:
        dict: Response with status, full message data, and request_id
    """
    request_id = set_request_id()

    try:
        service = get_gmail_service(profile)
        message = service.get_message(message_id)
        headers = service.get_message_headers(message)

        audit_logger.log_tool_call(
            tool_name="get_gmail_message",
            parameters={"message_id": message_id},
            request_id=request_id,
            success=True
        )

        return {
            "status": "success",
            "result": {
                "message": message,
                "headers": headers
            },
            "request_id": request_id
        }

    except Exception as e:
        error_msg = mask_credentials(str(e)) if should_sanitize() else str(e)

        audit_logger.log_tool_call(
            tool_name="get_gmail_message",
            parameters={"message_id": message_id},
            request_id=request_id,
            success=False,
            error_message=error_msg
        )

        return {
            "status": "error",
            "message": error_msg,
            "request_id": request_id
        }

    finally:
        clear_request_id()
```

## Step 5: Write Unit Tests

**File:** `tests/test_gmail_service.py` (new file)

```python
"""Tests for Gmail service."""

import pytest
from unittest.mock import MagicMock
from google_mcp_core.gmail import GmailService


def test_list_messages(mock_google_context):
    """Test listing Gmail messages."""
    # Arrange
    service = GmailService(mock_google_context)

    mock_response = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"}
        ],
        "resultSizeEstimate": 2
    }

    service.service.users().messages().list.return_value.execute.return_value = mock_response

    # Act
    messages = service.list_messages(query="is:unread", max_results=50)

    # Assert
    assert len(messages) == 2
    assert messages[0]["id"] == "msg1"

    # Verify API called correctly
    service.service.users().messages().list.assert_called_once()
    call_kwargs = service.service.users().messages().list.call_args[1]
    assert call_kwargs["userId"] == "me"
    assert call_kwargs["q"] == "is:unread"
    assert call_kwargs["maxResults"] == 50


def test_get_message(mock_google_context):
    """Test getting a Gmail message."""
    # Arrange
    service = GmailService(mock_google_context)

    mock_message = {
        "id": "msg123",
        "threadId": "thread456",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Subject"}
            ]
        }
    }

    service.service.users().messages().get.return_value.execute.return_value = mock_message

    # Act
    message = service.get_message("msg123")

    # Assert
    assert message["id"] == "msg123"
    assert len(message["payload"]["headers"]) == 2

    # Verify API called correctly
    service.service.users().messages().get.assert_called_once_with(
        userId="me",
        id="msg123",
        format="full"
    )


def test_get_message_headers(mock_google_context):
    """Test extracting headers from message."""
    # Arrange
    service = GmailService(mock_google_context)

    message = {
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Test Email"},
                {"name": "Date", "value": "Mon, 27 Jan 2024 10:00:00 +0000"}
            ]
        }
    }

    # Act
    headers = service.get_message_headers(message)

    # Assert
    assert headers["from"] == "sender@example.com"
    assert headers["subject"] == "Test Email"
    assert headers["date"] == "Mon, 27 Jan 2024 10:00:00 +0000"
```

**File:** `tests/conftest.py` (add Gmail mock fixture)

```python
@pytest.fixture
def mock_gmail_service(mock_google_context):
    """Create GmailService with mocked context."""
    from google_mcp_core.gmail import GmailService

    service = GmailService(mock_google_context)

    # Configure default mock responses
    service.service.users().messages().list.return_value.execute.return_value = {
        "messages": [],
        "resultSizeEstimate": 0
    }

    return service
```

## Step 6: Add CLI Commands

**File:** `src/google_mcp_core/cli.py`

```python
def cmd_gmail_list(args):
    """List Gmail messages."""
    try:
        service = get_gmail_service(args.profile)
        messages = service.list_messages(query=args.query, max_results=args.max_results)

        print(f"Found {len(messages)} messages:")
        for msg in messages:
            print(f"  - {msg['id']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_gmail_get(args):
    """Get Gmail message details."""
    try:
        service = get_gmail_service(args.profile)
        message = service.get_message(args.message_id)
        headers = service.get_message_headers(message)

        print(f"Message ID: {message['id']}")
        print(f"Thread ID: {message['threadId']}")
        print("\nHeaders:")
        for key, value in headers.items():
            print(f"  {key.title()}: {value}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# Register in COMMANDS dictionary
COMMANDS = {
    # ... existing command groups ...

    "gmail": {
        "list": {
            "handler": cmd_gmail_list,
            "help": "List Gmail messages",
            "args": [
                {"name": "--query", "default": "", "help": "Search query"},
                {"name": "--max-results", "type": int, "default": 100, "help": "Max messages"},
                {"name": "--profile", "default": "default", "help": "Profile name"}
            ]
        },
        "get": {
            "handler": cmd_gmail_get,
            "help": "Get Gmail message",
            "args": [
                {"name": "message_id", "help": "Message ID"},
                {"name": "--profile", "default": "default", "help": "Profile name"}
            ]
        }
    }
}
```

## Step 7: Update Documentation

**File:** `README.md`

Add to OAuth Scopes section:

```markdown
## OAuth Scopes

This server requires the following Google API scopes:

- `https://www.googleapis.com/auth/spreadsheets` - Read and write Google Sheets
- `https://www.googleapis.com/auth/drive` - Access Google Drive files and folders
- `https://www.googleapis.com/auth/gmail.readonly` - Read Gmail messages (read-only)

**Important:** If you previously authenticated and new scopes are added, you must
re-authenticate:

\```bash
rm ~/.config/google-personal-mcp/profiles/*/token.json
\```
```

Add to MCP Tools section:

```markdown
### list_gmail_messages

List Gmail messages matching search query.

**Parameters:**
- `query` (string, optional): Gmail search query
- `max_results` (int, optional): Maximum messages to return (default: 100)
- `profile` (string, optional): Authentication profile (default: "default")

### get_gmail_message

Get full Gmail message by ID.

**Parameters:**
- `message_id` (string): ID of message to retrieve
- `profile` (string, optional): Authentication profile (default: "default")
```

**File:** `docs/architecture.md`

Add to Service Layer section:

```markdown
### GmailService

Wraps Gmail API v1 operations:

- List messages with search queries
- Get full message details
- Extract message headers

**Design Principles:**
- One method per API operation
- Returns raw or lightly processed API responses
- Uses `@retry_on_rate_limit` for transient errors
- Helper methods for common operations
```

## Step 8: Run Tests and Verify

```bash
# Run unit tests
pytest tests/test_gmail_service.py -v
# Expected: All tests pass

# Test CLI commands
google-personal-mcp gmail list --query "is:unread" --max-results 10
google-personal-mcp gmail get msg_abc123

# Test MCP tools (via Claude or MCP client)
# list_gmail_messages(query="is:unread", max_results=10)
# get_gmail_message(message_id="msg_abc123")
```

## Step 9: Commit

```bash
git add -A
git commit -m "feat: add Gmail API integration

Adds support for Gmail API v1 with read-only access.

OAuth Scope Added:
- gmail.readonly

Components:
- GmailService class with list_messages() and get_message()
- MCP tools: list_gmail_messages, get_gmail_message
- CLI commands: gmail list, gmail get
- Unit tests with mocked Gmail API
- Documentation updated

Users must re-authenticate:
  rm ~/.config/google-personal-mcp/profiles/*/token.json

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Integration Checklist

- [ ] OAuth scope added to SCOPES list in auth.py
- [ ] Service class created following GoogleContext pattern
- [ ] Service uses `context.get_service(name, version)`
- [ ] API version explicitly specified (no "latest")
- [ ] Retry logic applied with `@retry_on_rate_limit`
- [ ] Service locator function added
- [ ] MCP tools follow standard template
- [ ] Unit tests written with mocked API
- [ ] CLI commands added
- [ ] README updated with OAuth scope and re-auth instructions
- [ ] Architecture documentation updated
- [ ] Implementation reference updated with patterns
- [ ] All tests passing
- [ ] Code formatted and linted

## See Also

- [Implementation Reference](../implementation-reference.md) - Google API integration patterns
- [Architecture](../architecture.md) - Service layer design
- [Definition of Done](../definition-of-done.md) - Complete checklist

---
Last Updated: 2026-01-27
