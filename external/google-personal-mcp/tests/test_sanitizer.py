"""Tests for credential sanitizer."""

from google_mcp_core.utils.sanitizer import (
    mask_credentials,
    should_sanitize,
    sanitize_parameters,
)


class TestMaskCredentials:
    """Test credential masking."""

    def test_mask_bearer_token(self):
        """Test masking Bearer tokens."""
        text = "Authorization: Bearer ya29.a0AfH6SMBx123xyz456..."
        masked = mask_credentials(text)

        assert "ya29" not in masked
        assert "***REDACTED***" in masked
        assert "Bearer" in masked

    def test_mask_oauth_token(self):
        """Test masking OAuth tokens."""
        text = "Token: ya29.a0AfH6SMBx123xyz456..."
        masked = mask_credentials(text)

        assert "ya29" not in masked
        assert "***OAUTH_TOKEN_REDACTED***" in masked

    def test_mask_api_key(self):
        """Test masking API keys."""
        text = "API key: AIzaSyDummy1234567890abcdefghijk"
        masked = mask_credentials(text)

        assert "AIza" not in masked
        # Either specific API key mask or generic ID mask is acceptable
        assert "***" in masked

    def test_mask_file_ids_full(self):
        """Test masking file IDs with full redaction."""
        text = "File ID: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8"
        masked = mask_credentials(text, partial=False)

        assert "1a2b3c" not in masked
        assert "***ID_REDACTED***" in masked

    def test_mask_file_ids_partial(self):
        """Test masking file IDs with partial display."""
        text = "File ID: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8"
        masked = mask_credentials(text, partial=True)

        assert "1a2..." in masked or "...q8" in masked  # Partial masking

    def test_non_string_input(self):
        """Test handling of non-string input."""
        result = mask_credentials(123)
        assert result == "123"

    def test_no_credentials_in_text(self):
        """Test text without credentials is unchanged."""
        text = "This is a normal message"
        masked = mask_credentials(text)

        assert masked == text

    def test_multiple_credentials(self):
        """Test masking multiple credentials in one text."""
        text = "Bearer ya29.xxx and file ID 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8"
        masked = mask_credentials(text)

        assert "ya29" not in masked
        assert "1a2b3c" not in masked
        # Count total replacements (should have at least 2 masks)
        assert masked.count("***") >= 2


class TestSanitizeParameters:
    """Test parameter sanitization."""

    def test_sanitize_content_parameter(self):
        """Test that content parameter is masked."""
        params = {"content": "This is secret content"}
        safe = sanitize_parameters(params)

        assert "secret content" not in safe["content"]
        assert "<" in safe["content"] and "bytes>" in safe["content"]

    def test_sanitize_local_path_parameter(self):
        """Test that local_path parameter is masked."""
        params = {"local_path": "/path/to/secret/file.txt"}
        safe = sanitize_parameters(params)

        assert "/path/to" not in safe["local_path"]
        assert "<" in safe["local_path"]

    def test_safe_parameters_pass_through(self):
        """Test that safe parameters are preserved."""
        params = {"sheet_alias": "prompts", "profile": "default"}
        safe = sanitize_parameters(params)

        assert safe["sheet_alias"] == "prompts"
        assert safe["profile"] == "default"

    def test_mixed_sensitive_and_safe_parameters(self):
        """Test handling mixed sensitive and safe parameters."""
        params = {"sheet_alias": "prompts", "content": "secret data", "profile": "default"}
        safe = sanitize_parameters(params)

        assert safe["sheet_alias"] == "prompts"
        assert safe["profile"] == "default"
        assert "secret data" not in safe["content"]


class TestShouldSanitize:
    """Test sanitization mode detection."""

    def test_should_sanitize_by_default(self, monkeypatch):
        """Test that sanitization is enabled by default."""
        monkeypatch.delenv("GOOGLE_PERSONAL_MCP_DEBUG", raising=False)
        assert should_sanitize() is True

    def test_should_not_sanitize_in_debug_mode(self, monkeypatch):
        """Test that sanitization is disabled in debug mode."""
        monkeypatch.setenv("GOOGLE_PERSONAL_MCP_DEBUG", "1")
        assert should_sanitize() is False

    def test_should_sanitize_debug_false(self, monkeypatch):
        """Test debug mode disabled via env var."""
        monkeypatch.setenv("GOOGLE_PERSONAL_MCP_DEBUG", "0")
        assert should_sanitize() is True
