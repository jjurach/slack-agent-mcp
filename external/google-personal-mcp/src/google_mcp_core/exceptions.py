"""Custom exception hierarchy for MCP server errors."""


class MCPServerException(Exception):
    """Base exception for MCP server errors."""

    pass


class ConfigurationError(MCPServerException):
    """Configuration loading or validation error."""

    pass


class AuthenticationError(MCPServerException):
    """Authentication/authorization failure."""

    pass


class AccessDeniedError(MCPServerException):
    """Access denied to resource."""

    pass


class GoogleAPIError(MCPServerException):
    """Google API call failed."""

    pass


class ResourceNotFoundError(MCPServerException):
    """Requested resource not found."""

    pass
