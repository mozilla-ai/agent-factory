"""Utility for retrying flaky tests with a minimum success threshold.

This module provides a decorator that runs a test function multiple times and passes only if
the function succeeds at least a specified number of times within the maximum attempts.
"""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from agent.utils.logging import logger

T = TypeVar("T")
ExceptionType = type[Exception] | tuple[type[Exception], ...]


def retry_with_threshold(
    max_attempts: int = 5, min_successes: int = 4, delay: float = 1.0, exceptions: ExceptionType = AssertionError
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that runs a test until it passes at least min_successes times out of max_attempts.

    Args:
        max_attempts: Maximum number of attempts to make (must be >= min_successes)
        min_successes: Minimum number of successful attempts required to pass (must be <= max_attempts)
        delay: Delay between attempts in seconds
        exceptions: Exception type or tuple of exception types to catch and retry on

    Returns:
        A decorated function that implements the retry logic

    Raises:
        ValueError: If max_attempts < min_successes or min_successes < 1
        Exception: The last exception raised by the test if it fails to meet the success threshold
    """
    if max_attempts < min_successes:
        raise ValueError(f"max_attempts ({max_attempts}) must be >= min_successes ({min_successes})")
    if min_successes < 1:
        raise ValueError(f"min_successes ({min_successes}) must be >= 1")

    # Convert single exception to tuple for consistent handling
    if isinstance(exceptions, type) and issubclass(exceptions, Exception):
        exceptions = (exceptions,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            successes = 0
            last_exception = None
            max_failures_allowed = max_attempts - min_successes

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    successes += 1
                    logger.info(
                        f"✅ Attempt {attempt}/{max_attempts} - Success! ({successes}/{min_successes} required)"
                    )

                    # Early exit if we've already reached the minimum required successes
                    if successes >= min_successes:
                        logger.info(
                            f"✅ Test passed with {successes} successful attempts out of {attempt} total attempts"
                        )
                        return result

                except exceptions as e:
                    last_exception = e
                    failures = attempt - successes

                    logger.error(f"❌ Attempt {attempt}/{max_attempts} failed: {str(e)}")

                    # Early exit if we can't reach min_successes in remaining attempts
                    if failures > max_failures_allowed:
                        break

                    if attempt < max_attempts:
                        time.sleep(delay)

            failures = attempt - successes
            error_msg = (
                f"Test failed with {successes} successes out of {attempt} attempts. "
                f"Required at least {min_successes} successes. "
                f"Last error: {str(last_exception) if last_exception else 'No error details available'}"
            )
            raise type(last_exception)(error_msg) from last_exception if last_exception else RuntimeError(error_msg)

        return wrapper

    return decorator
