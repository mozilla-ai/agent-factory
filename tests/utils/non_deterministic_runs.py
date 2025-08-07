"""Utility for running non-deterministic tests with a minimum success threshold.

This module provides a decorator that runs a test function multiple times and passes only if
the function succeeds at least a specified number of times within the maximum attempts.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from agent_factory.utils.logging import logger

T = TypeVar("T")
ExceptionType = type[Exception] | tuple[type[Exception], ...]


def run_until_success_threshold_async(
    exceptions: ExceptionType = (AssertionError, ValueError, RuntimeError, SyntaxError),
    concurrency_limit: int = 2,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Async decorator that runs a test until it passes at least min_successes times out of max_attempts.

    The decorator is configured via the test function's kwargs, which SHOULD include:
    - max_attempts: Maximum number of attempts to make (must be >= min_successes)
    - min_successes: Minimum number of successful attempts required (must be <= max_attempts)

    Args:
        exceptions: An exception or tuple of exceptions to catch and count as a failure.
        concurrency_limit: Maximum number of concurrent test runs.

    Returns:
        A decorated async function that implements the retry logic.

    Raises:
        ValueError: If max_attempts < min_successes or min_successes < 1.
        Exception: The last exception raised by the test if it fails to meet the success threshold.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            if "max_attempts" not in kwargs or "min_successes" not in kwargs:
                raise ValueError(
                    "Both 'max_attempts' and 'min_successes' must be provided in the test function's kwargs"
                )

            max_attempts = kwargs["max_attempts"]
            min_successes = kwargs["min_successes"]

            if max_attempts < min_successes:
                raise ValueError(f"max_attempts ({max_attempts}) must be >= min_successes ({min_successes})")
            if min_successes < 1:
                raise ValueError(f"min_successes ({min_successes}) must be >= 1")
            semaphore = asyncio.Semaphore(concurrency_limit)
            max_failures_allowed = max_attempts - min_successes

            async def single_attempt(attempt_num: int) -> Any:
                """Runs a single attempt of the decorated function, returning the result or exception."""
                async with semaphore:
                    logger.info(f"🔄 Starting attempt {attempt_num + 1}/{max_attempts}")
                    try:
                        if asyncio.iscoroutinefunction(func):
                            result = await func(*args, **kwargs)
                        else:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                        logger.info(f"✅ Attempt {attempt_num + 1}/{max_attempts} succeeded.")
                        return result
                    except exceptions as e:
                        logger.error(f"❌ Attempt {attempt_num + 1}/{max_attempts} failed: {e}")
                        return e

            tasks = [asyncio.create_task(single_attempt(i)) for i in range(max_attempts)]
            exceptions_list = []
            successes = 0
            successful_result = None

            try:
                for task_future in asyncio.as_completed(tasks):
                    result = await task_future
                    if isinstance(result, Exception):
                        exceptions_list.append(result)
                        failures = len(exceptions_list)
                        if failures > max_failures_allowed:
                            logger.warning("Test failing: success threshold can no longer be met.")
                            break  # No point in checking further, as we cannot reach min_successes
                    else:
                        successes += 1
                        if successful_result is None:
                            successful_result = result
                        if successes >= min_successes:
                            logger.info(f"✅ Test passed with {successes} successful attempts.")
                            return successful_result
            finally:
                # Cancel any outstanding tasks that are still running
                for task in tasks:
                    if not task.done():
                        task.cancel()
                # Wait for all tasks to complete (including cancelled ones) to avoid warnings
                await asyncio.gather(*tasks, return_exceptions=True)

            # If loop completes without meeting the threshold, display the errors encountered
            error_msg = [
                f"Test failed with {successes} successes out of {max_attempts} attempts. "
                f"Required at least {min_successes} successes."
            ]
            if exceptions_list:
                error_msg.append("\nErrors encountered:")
                for i, exc in enumerate(exceptions_list, 1):
                    error_msg.append(f"{i}. {exc}")

            final_error = "\n".join(error_msg)
            last_exception = exceptions_list[-1] if exceptions_list else RuntimeError(final_error)

            raise type(last_exception)(final_error) from last_exception

        return async_wrapper

    return decorator
