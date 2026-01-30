"""Request context management for tracing and correlation."""

import contextvars
import uuid
from typing import Optional

# Context variable for request ID (thread-safe, async-safe)
_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.

    Args:
        request_id: Explicit request ID, or None to generate UUID4

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    _request_id.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get current request ID.

    Returns:
        The current request ID or None if not set
    """
    return _request_id.get()


def clear_request_id() -> None:
    """Clear request ID for current context."""
    _request_id.set(None)
