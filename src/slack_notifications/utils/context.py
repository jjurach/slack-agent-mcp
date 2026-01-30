"""
Request context and ID management.

Provides context variables for tracking request IDs through the call chain.
"""

import contextvars
import uuid
from typing import Optional

# Context variable for request tracking
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'request_id', default=None
)


def set_request_id() -> str:
    """
    Set a unique request ID for context tracking.

    Returns:
        The newly generated request ID
    """
    request_id = str(uuid.uuid4())
    _request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        The current request ID, or None if not set
    """
    return _request_id_var.get()


def clear_request_id() -> None:
    """Clear the request ID from context."""
    _request_id_var.set(None)
