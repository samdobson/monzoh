"""Retry utilities for handling transient API errors."""

from __future__ import annotations

import asyncio
import random
import time
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from monzoh.exceptions import (
    MonzoNetworkError,
    MonzoRateLimitError,
    MonzoServerError,
    MonzoTimeoutError,
)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
        backoff_multiplier: Multiplier for exponential backoff
        max_delay: Maximum delay between retries in seconds
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exception types that should trigger retries
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type[Exception], ...] = (
            MonzoRateLimitError,
            MonzoServerError,
            MonzoTimeoutError,
            MonzoNetworkError,
        ),
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Optional delay from Retry-After header

        Returns:
            Delay in seconds before next retry
        """
        if retry_after is not None:
            return min(retry_after, self.max_delay)

        delay = self.base_delay * (self.backoff_multiplier**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            delay *= 0.5 + random.random() * 0.5  # noqa: S311

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised
            attempt: Current attempt number (0-indexed)

        Returns:
            True if the request should be retried, False otherwise
        """
        if attempt >= self.max_retries:
            return False

        return isinstance(exception, self.retryable_exceptions)

    def get_retry_after(self, exception: Exception) -> float | None:
        """Extract Retry-After value from rate limit exceptions.

        Args:
            exception: The exception that was raised

        Returns:
            Retry-After delay in seconds, or None if not available
        """
        if isinstance(exception, MonzoRateLimitError):
            # Check response headers first (standard HTTP Retry-After header)
            if hasattr(exception, "response_headers"):
                retry_after = exception.response_headers.get("retry-after")
                if retry_after is not None:
                    try:
                        return float(retry_after)
                    except (ValueError, TypeError):
                        pass

            # Fallback to response data for custom retry_after field
            if hasattr(exception, "response_data"):
                retry_after = exception.response_data.get("retry_after")
                if retry_after is not None:
                    try:
                        return float(retry_after)
                    except (ValueError, TypeError):
                        pass
        return None


def with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry logic to synchronous functions.

    Args:
        config: Retry configuration, defaults to RetryConfig()

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:  # noqa: PERF203
                    if not config.should_retry(e, attempt):
                        raise

                    retry_after = config.get_retry_after(e)
                    delay = config.calculate_delay(attempt, retry_after)

                    attempt += 1
                    time.sleep(delay)

        return wrapper

    return decorator


def with_async_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to add retry logic to asynchronous functions.

    Args:
        config: Retry configuration, defaults to RetryConfig()

    Returns:
        Decorated async function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:  # noqa: PERF203
                    if not config.should_retry(e, attempt):
                        raise

                    retry_after = config.get_retry_after(e)
                    delay = config.calculate_delay(attempt, retry_after)

                    attempt += 1
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
