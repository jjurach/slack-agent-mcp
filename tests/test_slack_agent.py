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
        self.agent = SlackAgent(self.token)

    def test_initialization(self):
        """Test SlackAgent initialization."""
        assert self.agent.token == self.token
        assert self.agent.rtm_client is not None
        assert self.agent.web_client is not None

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

    @patch('slack_agent.logger')
    def test_handle_hello(self, mock_logger):
        """Test RTM hello event handling."""
        payload = {"type": "hello"}

        self.agent.handle_hello(payload)

        # Verify log message contains expected content
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "[2025-12-25" in log_call  # Contains date
        assert "CST]" in log_call       # Contains timezone
        assert "RTM connection established" in log_call

    @patch('slack_agent.logger')
    def test_handle_goodbye(self, mock_logger):
        """Test RTM goodbye event handling."""
        payload = {"type": "goodbye"}

        self.agent.handle_goodbye(payload)

        # Verify log message contains expected content
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "[2025-12-25" in log_call  # Contains date
        assert "CST]" in log_call       # Contains timezone
        assert "RTM connection closed" in log_call

    @patch('slack_agent.logger')
    def test_handle_message_with_time_query(self, mock_logger):
        """Test message handling with time query."""
        payload = {
            "data": {
                "text": "what time is it?",
                "channel": "C1234567890",
                "user": "U1234567890",
                "ts": "1640995200.000100"
            }
        }

        with patch.object(self.agent, '_respond_with_time') as mock_respond:
            self.agent.handle_message(payload)

            # Verify message was logged
            assert mock_logger.info.call_count == 2  # One for message, one for potential response

            # Verify time response was triggered
            mock_respond.assert_called_once_with("C1234567890")

    @patch('slack_agent.logger')
    def test_handle_message_without_time_query(self, mock_logger):
        """Test message handling without time query."""
        payload = {
            "data": {
                "text": "hello world",
                "channel": "C1234567890",
                "user": "U1234567890",
                "ts": "1640995200.000100"
            }
        }

        with patch.object(self.agent, '_respond_with_time') as mock_respond:
            self.agent.handle_message(payload)

            # Verify message was logged
            mock_logger.info.assert_called_once()

            # Verify no time response was triggered
            mock_respond.assert_not_called()

    @patch('slack_agent.logger')
    def test_handle_message_error(self, mock_logger):
        """Test message handling with error."""
        payload = {"data": {}}  # Incomplete payload

        # Should not raise exception, but should log error
        self.agent.handle_message(payload)

        # Verify error was logged
        mock_logger.error.assert_called_once()

    @patch('slack_agent.logger')
    def test_start_success(self, mock_logger):
        """Test successful agent start."""
        # Mock RTM client
        self.agent.rtm_client = Mock()
        self.agent.rtm_client.start.return_value = None

        # Should complete without exception
        self.agent.start()

        # Verify startup log
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "Starting Slack Agent" in log_call

    @patch('slack_agent.logger')
    def test_start_keyboard_interrupt(self, mock_logger):
        """Test agent start with keyboard interrupt."""
        # Mock RTM client to raise KeyboardInterrupt
        self.agent.rtm_client = Mock()
        self.agent.rtm_client.start.side_effect = KeyboardInterrupt()

        # Should complete without exception
        self.agent.start()

        # Verify shutdown log
        mock_logger.info.assert_called_with("Slack Agent stopped by user")

    @patch('slack_agent.logger')
    def test_start_general_error(self, mock_logger):
        """Test agent start with general error."""
        # Mock RTM client to raise exception
        self.agent.rtm_client = Mock()
        self.agent.rtm_client.start.side_effect = Exception("Connection failed")

        # Should raise exception
        with pytest.raises(Exception):
            self.agent.start()

        # Verify error log
        mock_logger.error.assert_called_once()


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
        mock_agent_class.assert_called_once_with('xoxb-test-token')
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