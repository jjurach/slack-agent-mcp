"""Tests for custom exception hierarchy."""

import pytest
from google_mcp_core.exceptions import (
    MCPServerException,
    ConfigurationError,
    AuthenticationError,
    AccessDeniedError,
    GoogleAPIError,
    ResourceNotFoundError,
)


class TestExceptionHierarchy:
    """Test custom exception hierarchy."""

    def test_configuration_error_is_mcp_exception(self):
        """Test that ConfigurationError is subclass of MCPServerException."""
        assert issubclass(ConfigurationError, MCPServerException)

    def test_authentication_error_is_mcp_exception(self):
        """Test that AuthenticationError is subclass of MCPServerException."""
        assert issubclass(AuthenticationError, MCPServerException)

    def test_access_denied_error_is_mcp_exception(self):
        """Test that AccessDeniedError is subclass of MCPServerException."""
        assert issubclass(AccessDeniedError, MCPServerException)

    def test_google_api_error_is_mcp_exception(self):
        """Test that GoogleAPIError is subclass of MCPServerException."""
        assert issubclass(GoogleAPIError, MCPServerException)

    def test_resource_not_found_error_is_mcp_exception(self):
        """Test that ResourceNotFoundError is subclass of MCPServerException."""
        assert issubclass(ResourceNotFoundError, MCPServerException)

    def test_configuration_error_instantiation(self):
        """Test ConfigurationError can be instantiated with message."""
        error = ConfigurationError("Test config error")
        assert str(error) == "Test config error"

    def test_authentication_error_instantiation(self):
        """Test AuthenticationError can be instantiated with message."""
        error = AuthenticationError("Test auth error")
        assert str(error) == "Test auth error"

    def test_mcp_exception_is_exception(self):
        """Test that MCPServerException is subclass of Exception."""
        assert issubclass(MCPServerException, Exception)

    def test_raise_and_catch_configuration_error(self):
        """Test raising and catching ConfigurationError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config failed")

    def test_raise_and_catch_authentication_error(self):
        """Test raising and catching AuthenticationError."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Auth failed")

    def test_catch_mcp_exception_catches_subclass(self):
        """Test that catching MCPServerException catches subclasses."""
        with pytest.raises(MCPServerException):
            raise ConfigurationError("Config error")
