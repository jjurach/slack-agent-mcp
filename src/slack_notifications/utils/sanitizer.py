"""
Credential sanitization utilities.

Prevents sensitive information (Slack tokens, webhook URLs) from appearing in logs.
"""

import os
import re
from typing import Any, Dict, Union


def should_sanitize() -> bool:
    """
    Check if credential sanitization should be enabled.

    Returns:
        True if credentials should be masked, False if debug mode is enabled
    """
    return os.getenv("SLACK_AGENT_DEBUG", "0") != "1"


def mask_credentials(text: str) -> str:
    """
    Mask sensitive credentials in text.

    Patterns masked:
    - Slack bot tokens (xoxb-*)
    - Slack user tokens (xoxp-*)
    - Slack app tokens (xapp-*)
    - Slack webhook URLs

    Args:
        text: Text potentially containing credentials

    Returns:
        Text with credentials masked

    Example:
        >>> mask_credentials("Token: xoxb-1234567890-abcdefg")
        "Token: xoxb-****-****"
    """
    if not should_sanitize():
        return text

    # Mask Slack bot tokens
    text = re.sub(
        r'xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+',
        'xoxb-****-****',
        text
    )

    # Mask Slack user tokens
    text = re.sub(
        r'xoxp-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9]+',
        'xoxp-****-****-****',
        text
    )

    # Mask Slack app tokens
    text = re.sub(
        r'xapp-[0-9]+-[A-Z0-9]+-[0-9]+-[a-z0-9]+',
        'xapp-****-****-****-****',
        text
    )

    # Mask webhook URLs
    text = re.sub(
        r'https://hooks\.slack\.com/services/[A-Z0-9]+/[A-Z0-9]+/[a-zA-Z0-9]+',
        'https://hooks.slack.com/services/****',
        text
    )

    return text


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary containing potential credentials.

    Args:
        data: Dictionary to sanitize

    Returns:
        Dictionary with credentials masked
    """
    if not should_sanitize():
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = mask_credentials(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item) if isinstance(item, dict)
                else mask_credentials(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result
