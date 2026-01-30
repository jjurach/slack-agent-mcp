"""Retry decorator with exponential backoff for API calls."""

import time
import logging
import random
from functools import wraps
from typing import Callable, Type, Tuple, TypeVar, Any

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for delay between retries (default: 2.0 for exponential)
        initial_delay: Initial delay in seconds (default: 1.0)
        jitter: Add randomness to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exceptions to retry on (default: Exception)

    Returns:
        Decorated function that retries on failure
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise

                    # Calculate backoff with optional jitter
                    if jitter:
                        # Add randomness: delay * (0.5 to 1.5)
                        actual_delay = delay * (0.5 + random.random())
                    else:
                        actual_delay = delay

                    logger.debug(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )

                    time.sleep(actual_delay)
                    delay *= backoff_factor

            # Should not reach here, but just in case
            raise last_exception

        return wrapper

    return decorator
