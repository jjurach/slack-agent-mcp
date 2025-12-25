"""
Unit tests for the Slack Agent script.

This module tests the SlackAgent class and its time query functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import pytz

from slack_agent import SlackAgent, CST


class TestSlackAgent:
    """Test the SlackAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token = "xoxb-test-token"
        self.agent = SlackAgent(self.token, channels=["C123456"], poll_interval=1)

    def test_initialization(self):
        """Test SlackAgent initialization."""
        assert self.agent.token == self.token
        assert self.agent.web_client is not None
        assert self.agent.channels == ["C123456"]
        assert self.agent.poll_interval == 1
        assert self.agent.last_timestamps == {}
        assert self.agent.bot_user_id is None

    def test_is_time_query_positive_cases(self):
        """Test time query detection with positive cases."""
        time_queries = [
            "what time is it",
            "what time is it?",
            "what's the time",
            "what's the time?",
            "what is the time",
            "what is the time?",
            "time",
            "current time",
            "What time is it?",  # Mixed case
            "WHAT TIME IS IT",   # Upper case
        ]

        for query in time_queries:
            assert self.agent._is_time_query(query), f"Failed to detect: {query}"

    def test_is_time_query_negative_cases(self):
        """Test time query detection with negative cases."""
        non_time_queries = [
            "what time was it",
            "what's the weather",
            "show me the time",
            "tell me what time it is",
            "hello",
            "how are you",
            "good morning",
            "",
            "what's for lunch",
        ]

        for query in non_time_queries:
            assert not self.agent._is_time_query(query), f"Incorrectly detected: {query}"

    @patch('slack_agent.datetime')
    def test_respond_with_time(self, mock_datetime):
        """Test time response functionality."""
        # Setup mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "11:00:00 AM CST on 2025-12-25"
        mock_datetime.now.return_value = mock_now

        # Setup mock web client
        self.agent.web_client = Mock()
        self.agent.web_client.chat_postMessage.return_value = {"ok": True}

        # Test
        self.agent._respond_with_time("C1234567890")

        # Assertions
        self.agent.web_client.chat_postMessage.assert_called_once_with(
            channel="C1234567890",
            text="The current time is 11:00:00 AM CST on 2025-12-25"
        )

    @patch('slack_agent.datetime')
    @patch('slack_agent.logger')
    def test_respond_with_time_error(self, mock_logger, mock_datetime):
        """Test time response with error handling."""
        # Setup mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "11:00:00 AM CST on 2025-12-25"
        mock_datetime.now.return_value = mock_now

        # Setup mock web client to raise exception
        self.agent.web_client = Mock()
        self.agent.web_client.chat_postMessage.side_effect = Exception("API Error")

        # Test
        self.agent._respond_with_time("C1234567890")

        # Assertions - should not raise, but should log error
        mock_logger.error.assert_called_once()

    @patch('slack_agent.SlackApiError')
    def test_get_channels_to_monitor_specified_channels(self, mock_slack_error):
        """Test getting channels when channels are specified."""
        self.agent.channels = ["C123", "C456"]
        channels = self.agent._get_channels_to_monitor()
        assert channels == ["C123", "C456"]

    @patch('slack_agent.SlackApiError')
    def test_get_channels_to_monitor_auto_detect(self, mock_slack_error):
        """Test getting channels with auto-detection."""
        self.agent.channels = []

        # Mock the API response
        mock_response = {
            "ok": True,
            "channels": [
                {"id": "C001", "name": "random"},
                {"id": "C002", "name": "general"},
                {"id": "C003", "name": "another-general"},
                {"id": "C004", "name": "private"}
            ]
        }
        self.agent.web_client.conversations_list.return_value = mock_response

        channels = self.agent._get_channels_to_monitor()
        assert channels == ["C002", "C003"]  # Should prefer general channels

    @patch('slack_agent.SlackApiError')
    def test_get_channels_to_monitor_api_error(self, mock_slack_error):
        """Test getting channels with API error."""
        self.agent.channels = []

        # Mock API error
        mock_slack_error.return_value.response = {"error": "not_allowed"}
        self.agent.web_client.conversations_list.side_effect = mock_slack_error

        channels = self.agent._get_channels_to_monitor()
        assert channels == []

    def test_get_bot_user_id_success(self):
        """Test getting bot user ID successfully."""
        mock_response = {"ok": True, "user_id": "U123456"}
        self.agent.web_client.auth_test.return_value = mock_response

        user_id = self.agent._get_bot_user_id()
        assert user_id == "U123456"

    def test_get_bot_user_id_error(self):
        """Test getting bot user ID with error."""
        from slack_sdk.errors import SlackApiError
        mock_error = SlackApiError("Auth failed", {"error": "invalid_auth"})
        self.agent.web_client.auth_test.side_effect = mock_error

        user_id = self.agent._get_bot_user_id()
        assert user_id is None

    @patch('slack_agent.logger')
    def test_poll_messages_with_time_query(self, mock_logger):
        """Test polling messages with time query."""
        # Setup agent
        self.agent.bot_user_id = "U999999"
        self.agent.last_timestamps = {}

        # Mock API responses
        history_response = {
            "ok": True,
            "messages": [
                {
                    "ts": "1640995200.000200",
                    "user": "U1234567890",
                    "text": "what time is it?"
                }
            ]
        }
        self.agent.web_client.conversations_history.return_value = history_response

        with patch.object(self.agent, '_respond_with_time') as mock_respond:
            self.agent._poll_messages()

            # Verify message was logged
            mock_logger.info.assert_called()
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("MESSAGE" in call and "what time is it?" in call for call in log_calls)

            # Verify time response was triggered
            mock_respond.assert_called_once_with("C123456")

    @patch('slack_agent.logger')
    def test_poll_messages_without_time_query(self, mock_logger):
        """Test polling messages without time query."""
        # Setup agent
        self.agent.bot_user_id = "U999999"
        self.agent.last_timestamps = {}

        # Mock API responses
        history_response = {
            "ok": True,
            "messages": [
                {
                    "ts": "1640995200.000200",
                    "user": "U1234567890",
                    "text": "hello world"
                }
            ]
        }
        self.agent.web_client.conversations_history.return_value = history_response

        with patch.object(self.agent, '_respond_with_time') as mock_respond:
            self.agent._poll_messages()

            # Verify message was logged
            mock_logger.info.assert_called()

            # Verify no time response was triggered
            mock_respond.assert_not_called()

    @patch('slack_agent.logger')
    def test_poll_messages_skip_bot_messages(self, mock_logger):
        """Test polling messages skips bot's own messages."""
        # Setup agent
        self.agent.bot_user_id = "U1234567890"  # Bot's own user ID
        self.agent.last_timestamps = {}

        # Mock API responses
        history_response = {
            "ok": True,
            "messages": [
                {
                    "ts": "1640995200.000200",
                    "user": "U1234567890",  # Bot's own message
                    "text": "what time is it?"
                }
            ]
        }
        self.agent.web_client.conversations_history.return_value = history_response

        with patch.object(self.agent, '_respond_with_time') as mock_respond:
            self.agent._poll_messages()

            # Verify no time response was triggered (bot ignores its own messages)
            mock_respond.assert_not_called()

    @patch('slack_agent.logger')
    @patch('slack_agent.time.sleep')
    def test_start_success(self, mock_sleep, mock_logger):
        """Test successful agent start."""
        # Mock authentication
        self.agent.web_client.auth_test.return_value = {"ok": True, "user_id": "U123456"}

        # Mock polling to avoid infinite loop
        with patch.object(self.agent, '_poll_messages') as mock_poll:
            mock_poll.side_effect = KeyboardInterrupt()  # Stop after first poll

            # Should complete without exception
            self.agent.start()

            # Verify startup logs
            assert mock_logger.info.call_count >= 2  # At least startup and bot user logs

    @patch('slack_agent.logger')
    def test_start_auth_failure(self, mock_logger):
        """Test agent start with authentication failure."""
        # Mock authentication failure
        self.agent.web_client.auth_test.return_value = {"ok": False}

        # Should raise exception
        with pytest.raises(Exception, match="Could not authenticate bot user"):
            self.agent.start()

    @patch('slack_agent.logger')
    @patch('slack_agent.time.sleep')
    def test_start_keyboard_interrupt(self, mock_sleep, mock_logger):
        """Test agent start with keyboard interrupt."""
        # Mock authentication
        self.agent.web_client.auth_test.return_value = {"ok": True, "user_id": "U123456"}

        # Mock polling to raise KeyboardInterrupt
        with patch.object(self.agent, '_poll_messages') as mock_poll:
            mock_poll.side_effect = KeyboardInterrupt()

            # Should complete without exception
            self.agent.start()

            # Verify shutdown log
            shutdown_logs = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("stopped by user" in log for log in shutdown_logs)

    @patch('slack_agent.logger')
    def test_start_general_error(self, mock_logger):
        """Test agent start with general error."""
        # Mock authentication
        self.agent.web_client.auth_test.return_value = {"ok": True, "user_id": "U123456"}

        # Mock polling to raise exception
        with patch.object(self.agent, '_poll_messages') as mock_poll:
            mock_poll.side_effect = Exception("Polling failed")

            # Should raise exception
            with pytest.raises(Exception, match="Polling failed"):
                self.agent.start()


class TestCSTTimezone:
    """Test CST timezone functionality."""

    def test_cst_timezone(self):
        """Test that CST timezone is properly configured."""
        assert CST is not None
        assert CST.zone == "America/Chicago"

    def test_cst_conversion(self):
        """Test CST time conversion."""
        # Create a UTC time
        utc_time = datetime(2025, 12, 25, 17, 0, 0)  # 5 PM UTC
        utc_time = pytz.utc.localize(utc_time)

        # Convert to CST (UTC-6)
        cst_time = utc_time.astimezone(CST)
        assert cst_time.hour == 11  # Should be 11 AM CST
        assert cst_time.day == 25
        assert cst_time.month == 12


class TestMainFunction:
    """Test the main function."""

    @patch('slack_agent.SlackAgent')
    @patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test-token'})
    def test_main_success(self, mock_agent_class):
        """Test successful main execution."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        from slack_agent import main

        main()

        # Verify agent was created and started
        mock_agent_class.assert_called_once_with('xoxb-test-token', channels=None, poll_interval=5)
        mock_agent.start.assert_called_once()

    @patch.dict('os.environ', {}, clear=True)
    def test_main_missing_token(self):
        """Test main with missing bot token."""
        from slack_agent import main
        import sys
        from unittest.mock import patch

        with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
            main()

            mock_print.assert_called_once_with("Error: SLACK_BOT_TOKEN environment variable is required")
            mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    pytest.main([__file__])