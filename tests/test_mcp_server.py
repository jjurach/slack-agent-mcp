"""
Unit tests for the Slack MCP server.

This module tests the FastMCP server functionality for Slack notifications.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from slack_notifications.mcp_server import (
    send_slack_message,
    send_slack_success,
    send_slack_warning,
    send_slack_error,
    configure_slack_notifications
)


class TestMCPTools:
    """Test the MCP tool functions."""

    @patch('slack_notifications.mcp_server.SlackNotifier')
    def test_send_slack_message_success(self, mock_notifier_class):
        """Test successful message sending."""
        # Setup mock
        mock_notifier = Mock()
        mock_notifier.notify.return_value = {"ok": True, "channel": "C1234567890"}
        mock_notifier.config.default_channel = "#general"
        mock_notifier_class.return_value = mock_notifier

        # Test
        result = send_slack_message("Test message", "#test", "info")

        # Assertions
        assert "✅ Message sent successfully to #test" in result
        mock_notifier_class.assert_called_once()
        mock_notifier.notify.assert_called_once_with(
            message="Test message",
            channel="#test",
            level="info"
        )

    @patch('slack_notifications.mcp_server.SlackNotifier')
    def test_send_slack_message_default_channel(self, mock_notifier_class):
        """Test message sending with default channel."""
        # Setup mock
        mock_notifier = Mock()
        mock_notifier.notify.return_value = {"ok": True, "channel": "C1234567890"}
        mock_notifier.config.default_channel = "#general"
        mock_notifier_class.return_value = mock_notifier

        # Test
        result = send_slack_message("Test message")

        # Assertions
        assert "✅ Message sent successfully to #general" in result
        mock_notifier.notify.assert_called_once_with(
            message="Test message",
            channel=None,
            level="info"
        )

    @patch('slack_notifications.mcp_server.SlackNotifier')
    @patch('slack_notifications.mcp_server.logger')
    def test_send_slack_message_config_error(self, mock_logger, mock_notifier_class):
        """Test message sending with configuration error."""
        from slack_notifications.exceptions import SlackConfigError

        # Setup mock to raise config error
        mock_notifier_class.side_effect = SlackConfigError("No configuration found")

        # Test
        with pytest.raises(ValueError) as exc_info:
            send_slack_message("Test message")

        # Assertions
        assert "❌ Slack configuration error" in str(exc_info.value)
        mock_logger.error.assert_called_once()

    @patch('slack_notifications.mcp_server.SlackNotifier')
    @patch('slack_notifications.mcp_server.logger')
    def test_send_slack_message_notification_error(self, mock_logger, mock_notifier_class):
        """Test message sending with notification error."""
        from slack_notifications.exceptions import SlackNotificationError

        # Setup mock
        mock_notifier = Mock()
        mock_notifier.notify.side_effect = SlackNotificationError("API Error")
        mock_notifier_class.return_value = mock_notifier

        # Test
        with pytest.raises(ValueError) as exc_info:
            send_slack_message("Test message")

        # Assertions
        assert "❌ Failed to send Slack message" in str(exc_info.value)
        mock_logger.error.assert_called_once()

    def test_send_slack_success(self):
        """Test send_slack_success convenience function."""
        with patch('slack_notifications.mcp_server.send_slack_message') as mock_send:
            mock_send.return_value = "✅ Message sent successfully to #test"

            result = send_slack_success("Success message", "#test")

            mock_send.assert_called_once_with("Success message", "#test", "success")
            assert result == "✅ Message sent successfully to #test"

    def test_send_slack_warning(self):
        """Test send_slack_warning convenience function."""
        with patch('slack_notifications.mcp_server.send_slack_message') as mock_send:
            mock_send.return_value = "✅ Message sent successfully to #test"

            result = send_slack_warning("Warning message", "#test")

            mock_send.assert_called_once_with("Warning message", "#test", "warning")
            assert result == "✅ Message sent successfully to #test"

    def test_send_slack_error(self):
        """Test send_slack_error convenience function."""
        with patch('slack_notifications.mcp_server.send_slack_message') as mock_send:
            mock_send.return_value = "✅ Message sent successfully to #test"

            result = send_slack_error("Error message", "#test")

            mock_send.assert_called_once_with("Error message", "#test", "error")
            assert result == "✅ Message sent successfully to #test"

    @patch('slack_notifications.notifier.configure')
    def test_configure_slack_notifications_success(self, mock_configure):
        """Test successful configuration."""
        result = configure_slack_notifications(
            bot_token="xoxb-test-token",
            default_channel="#test",
            timeout=60,
            max_retries=5
        )

        assert result == "✅ Slack notifications configured successfully"
        mock_configure.assert_called_once_with(
            bot_token="xoxb-test-token",
            default_channel="#test",
            timeout=60,
            max_retries=5
        )

    @patch('slack_notifications.notifier.configure')
    @patch('slack_notifications.mcp_server.logger')
    def test_configure_slack_notifications_error(self, mock_logger, mock_configure):
        """Test configuration with error."""
        from slack_notifications.exceptions import SlackConfigError

        mock_configure.side_effect = SlackConfigError("Invalid token")

        with pytest.raises(ValueError) as exc_info:
            configure_slack_notifications(bot_token="invalid-token")

        assert "❌ Configuration failed" in str(exc_info.value)
        mock_logger.error.assert_called_once()


class TestMCPIntegration:
    """Test MCP server integration."""

    @patch('slack_notifications.mcp_server.mcp')
    @patch('slack_notifications.mcp_server.logger')
    def test_main_function(self, mock_logger, mock_mcp):
        """Test the main function starts the MCP server."""
        from slack_notifications.mcp_server import main

        # Mock the async run
        mock_mcp.run = Mock()

        with patch('asyncio.run') as mock_asyncio_run:
            main()

            mock_asyncio_run.assert_called_once()
            mock_logger.info.assert_called_once_with("Starting Slack MCP server...")

    @patch('slack_notifications.mcp_server.mcp')
    def test_mcp_server_initialization(self, mock_mcp):
        """Test that MCP server is properly initialized."""
        # Import the module to trigger initialization
        import slack_notifications.mcp_server

        # Verify FastMCP was called with correct parameters
        mock_mcp.assert_called_once_with(
            "slack-notifications",
            description="Send notifications to Slack channels via MCP protocol"
        )


if __name__ == "__main__":
    pytest.main([__file__])