"""Utility for sanitizing credentials from logs and error messages."""

import re
import os


def should_sanitize() -> bool:
    """
    Check if logs should be sanitized (not in debug mode).

    Returns:
        True if logs should be sanitized, False in debug mode
    """
    debug_mode = os.getenv("GOOGLE_PERSONAL_MCP_DEBUG", "").lower() in ("1", "true", "yes")
    return not debug_mode


def mask_credentials(text: str, partial: bool = False) -> str:
    """
    Replace credentials and sensitive data with redaction markers.

    Args:
        text: Text that may contain credentials
        partial: If True, show first/last chars (e.g., "12..78" for "1234567890")

    Returns:
        Sanitized text with credentials replaced
    """
    if not isinstance(text, str):
        return str(text)

    # Mask Bearer tokens: "Bearer ya29.xxxxx" -> "Bearer ***REDACTED***"
    text = re.sub(r"(Bearer\s+)[A-Za-z0-9._-]+", r"\1***REDACTED***", text, flags=re.IGNORECASE)

    # Mask Google API keys (AIza... format)
    text = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "***API_KEY_REDACTED***", text)

    # Mask OAuth tokens (ya29... format)
    text = re.sub(r"ya29\.[A-Za-z0-9_-]+", "***OAUTH_TOKEN_REDACTED***", text)

    # Mask file/folder IDs (usually 20+ alphanumeric chars)
    if partial:
        # Show pattern like: "1a2...xyz" (first 3, last 3)
        text = re.sub(
            r"([0-9a-zA-Z_-]{25,})", lambda m: m.group(1)[:3] + "..." + m.group(1)[-3:], text
        )
    else:
        # Full redaction (only if string looks like ID, not normal text)
        text = re.sub(r"[0-9a-zA-Z_-]{25,}", "***ID_REDACTED***", text)

    return text


def sanitize_parameters(params: dict) -> dict:
    """
    Remove/mask sensitive parameters before logging.

    Args:
        params: Dictionary of parameters

    Returns:
        Sanitized parameters safe for logging
    """
    safe = {}
    sensitive_keys = {"content", "local_path", "access_token", "refresh_token", "credentials"}

    for key, value in params.items():
        if key in sensitive_keys:
            # Log type and size but not content
            safe[key] = f"<{type(value).__name__}: {len(str(value))} bytes>"
        else:
            # Safe to log
            safe[key] = mask_credentials(str(value)) if isinstance(value, str) else value

    return safe
