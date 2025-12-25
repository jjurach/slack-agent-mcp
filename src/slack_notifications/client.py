"""
Slack client implementation with error handling and retry logic.

This module provides a wrapper around the slack-sdk with comprehensive
error handling, retry logic, and proper logging.
"""

import asyncio
import logging
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .config import SlackConfig
from .exceptions import SlackAPIError, SlackNetworkError

logger = logging.getLogger(__name__)


class SlackClient:
    """
    Enhanced Slack Web API client with error handling and retry logic.

    This client wraps the official slack-sdk WebClient with:
    - Automatic retry on rate limits and transient errors
    - Comprehensive error handling and logging
    - Async support
    """

    def __init__(self, config: SlackConfig):
        """
        Initialize the Slack client.

        Args:
            config: Slack configuration object
        """
        self.config = config
        self._client = WebClient(token=config.bot_token, timeout=config.timeout)

        # Configure logging
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should trigger a retry.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_retries:
            return False

        # Retry on rate limiting
        if isinstance(error, SlackApiError):
            if error.response and error.response.get("error") == "rate_limited":
                return True
            # Don't retry on authentication or permission errors
            if error.response and error.response.get("error") in [
                "invalid_auth",
                "missing_scope",
                "channel_not_found",
                "not_in_channel",
            ]:
                return False

        # Retry on network-related errors
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return True

        return False

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate backoff delay for retry attempts.

        Uses exponential backoff with jitter.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        import random
        import time

        # Exponential backoff: 1, 2, 4, 8... seconds
        base_delay = 2 ** attempt

        # Add jitter (±25%)
        jitter = random.uniform(-0.25, 0.25) * base_delay
        delay = base_delay + jitter

        # Cap at 30 seconds
        return min(delay, 30.0)

    def post_message(
        self,
        channel: str,
        text: str,
        **kwargs
    ) -> dict:
        """
        Send a message to a Slack channel with retry logic.

        Args:
            channel: Channel to post to (e.g., "#general" or "@user")
            text: Message text
            **kwargs: Additional arguments for chat_postMessage API

        Returns:
            API response dictionary

        Raises:
            SlackAPIError: For Slack API errors (after retries)
            SlackNetworkError: For network errors (after retries)
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Posting message to {channel} (attempt {attempt + 1})")

                response = self._client.chat_postMessage(
                    channel=channel,
                    text=text,
                    **kwargs
                )

                logger.info(f"Successfully posted message to {channel}")
                return response

            except SlackApiError as e:
                last_error = e
                error_type = e.response.get("error", "unknown") if e.response else "unknown"

                if self._should_retry(e, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Slack API error (attempt {attempt + 1}/{self.config.max_retries + 1}): "
                        f"{error_type}. Retrying in {delay:.1f}s..."
                    )
                    asyncio.sleep(delay) if asyncio.iscoroutinefunction(asyncio.sleep) else time.sleep(delay)
                    continue

                logger.error(f"Slack API error: {error_type}")
                raise SlackAPIError(f"Slack API error: {error_type}", e) from e

            except (ConnectionError, TimeoutError, OSError) as e:
                last_error = e

                if self._should_retry(e, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Network error (attempt {attempt + 1}/{self.config.max_retries + 1}): "
                        f"{e}. Retrying in {delay:.1f}s..."
                    )
                    asyncio.sleep(delay) if asyncio.iscoroutinefunction(asyncio.sleep) else time.sleep(delay)
                    continue

                logger.error(f"Network error: {e}")
                raise SlackNetworkError(f"Network error: {e}", e) from e

        # This should never be reached, but just in case
        raise SlackAPIError("Max retries exceeded", last_error) from last_error

    async def post_message_async(
        self,
        channel: str,
        text: str,
        **kwargs
    ) -> dict:
        """
        Send a message to a Slack channel asynchronously with retry logic.

        Args:
            channel: Channel to post to (e.g., "#general" or "@user")
            text: Message text
            **kwargs: Additional arguments for chat_postMessage API

        Returns:
            API response dictionary

        Raises:
            SlackAPIError: For Slack API errors (after retries)
            SlackNetworkError: For network errors (after retries)
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(f"Posting message to {channel} async (attempt {attempt + 1})")

                # Use asyncio.to_thread for the synchronous slack-sdk call
                response = await asyncio.to_thread(
                    self._client.chat_postMessage,
                    channel=channel,
                    text=text,
                    **kwargs
                )

                logger.info(f"Successfully posted message to {channel} (async)")
                return response

            except SlackApiError as e:
                last_error = e
                error_type = e.response.get("error", "unknown") if e.response else "unknown"

                if self._should_retry(e, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Slack API error async (attempt {attempt + 1}/{self.config.max_retries + 1}): "
                        f"{error_type}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue

                logger.error(f"Slack API error async: {error_type}")
                raise SlackAPIError(f"Slack API error: {error_type}", e) from e

            except (ConnectionError, TimeoutError, OSError) as e:
                last_error = e

                if self._should_retry(e, attempt):
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(
                        f"Network error async (attempt {attempt + 1}/{self.config.max_retries + 1}): "
                        f"{e}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue

                logger.error(f"Network error async: {e}")
                raise SlackNetworkError(f"Network error: {e}", e) from e

        # This should never be reached, but just in case
        raise SlackAPIError("Max retries exceeded", last_error) from last_error