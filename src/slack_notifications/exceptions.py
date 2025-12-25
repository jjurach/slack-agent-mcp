"""
Custom exceptions for Slack notifications.
"""


class SlackNotificationError(Exception):
    """
    Base exception for Slack notification errors.

    This exception is raised when there are issues with sending
    Slack notifications, such as configuration errors, network issues,
    or Slack API errors.
    """

    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            original_error: The original exception that caused this error (optional)
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self):
        if self.original_error:
            return f"{self.message} (Original error: {self.original_error})"
        return self.message


class SlackConfigError(SlackNotificationError):
    """
    Exception raised for configuration-related errors.

    This includes missing or invalid configuration values,
    malformed config files, etc.
    """
    pass


class SlackAPIError(SlackNotificationError):
    """
    Exception raised for Slack API-related errors.

    This includes authentication failures, rate limiting,
    invalid channel names, etc.
    """
    pass


class SlackNetworkError(SlackNotificationError):
    """
    Exception raised for network-related errors.

    This includes connection timeouts, DNS resolution failures,
    SSL certificate issues, etc.
    """
    pass