"""Tests for retry functionality."""

from unittest.mock import Mock, patch

import pytest

from monzoh.core.retry import RetryConfig, with_async_retry, with_retry
from monzoh.exceptions import (
    MonzoNetworkError,
    MonzoRateLimitError,
    MonzoServerError,
    MonzoTimeoutError,
)


class TestRetryConfig:
    """Test RetryConfig class."""

    def test_default_configuration(self) -> None:
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.backoff_multiplier == 2.0
        assert config.max_delay == 60.0
        assert config.jitter is True
        assert config.retryable_exceptions == (
            MonzoRateLimitError,
            MonzoServerError,
            MonzoTimeoutError,
            MonzoNetworkError,
        )

    def test_custom_configuration(self) -> None:
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            backoff_multiplier=1.5,
            max_delay=30.0,
            jitter=False,
            retryable_exceptions=(MonzoRateLimitError,),
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.backoff_multiplier == 1.5
        assert config.max_delay == 30.0
        assert config.jitter is False
        assert config.retryable_exceptions == (MonzoRateLimitError,)

    def test_calculate_delay_without_jitter(self) -> None:
        """Test delay calculation without jitter."""
        config = RetryConfig(base_delay=1.0, backoff_multiplier=2.0, jitter=False)

        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_with_max_delay(self) -> None:
        """Test delay calculation respects max_delay."""
        config = RetryConfig(base_delay=10.0, max_delay=15.0, jitter=False)

        assert config.calculate_delay(0) == 10.0
        assert config.calculate_delay(1) == 15.0  # Capped at max_delay
        assert config.calculate_delay(2) == 15.0  # Capped at max_delay

    def test_calculate_delay_with_jitter(self) -> None:
        """Test delay calculation with jitter."""
        config = RetryConfig(base_delay=2.0, jitter=True)

        # With jitter, delay should be between 50% and 100% of calculated delay
        delay = config.calculate_delay(0)
        assert 1.0 <= delay <= 2.0

    def test_calculate_delay_with_retry_after(self) -> None:
        """Test delay calculation with Retry-After header."""
        config = RetryConfig(base_delay=10.0, max_delay=60.0)

        # Retry-After should override calculated delay
        assert config.calculate_delay(0, retry_after=5.0) == 5.0

        # But still respect max_delay
        assert config.calculate_delay(0, retry_after=100.0) == 60.0

    def test_should_retry_success_cases(self) -> None:
        """Test should_retry for retryable exceptions."""
        config = RetryConfig(max_retries=3)

        retryable_exceptions = [
            MonzoRateLimitError("Rate limited"),
            MonzoServerError("Server error"),
            MonzoTimeoutError("Timeout"),
            MonzoNetworkError("Network error"),
        ]

        for exc in retryable_exceptions:
            assert config.should_retry(exc, 0) is True
            assert config.should_retry(exc, 1) is True
            assert config.should_retry(exc, 2) is True

    def test_should_retry_max_attempts_exceeded(self) -> None:
        """Test should_retry when max attempts exceeded."""
        config = RetryConfig(max_retries=2)
        exc = MonzoRateLimitError("Rate limited")

        assert config.should_retry(exc, 0) is True
        assert config.should_retry(exc, 1) is True
        assert config.should_retry(exc, 2) is False  # Exceeded max_retries

    def test_should_retry_non_retryable_exception(self) -> None:
        """Test should_retry for non-retryable exceptions."""
        config = RetryConfig()
        exc = ValueError("Not retryable")

        assert config.should_retry(exc, 0) is False

    def test_get_retry_after_from_headers(self) -> None:
        """Test extracting Retry-After from response headers."""
        config = RetryConfig()

        # Create exception with response headers
        exc = MonzoRateLimitError("Rate limited")
        exc.response_headers = {"retry-after": "30"}

        assert config.get_retry_after(exc) == 30.0

    def test_get_retry_after_from_response_data(self) -> None:
        """Test extracting Retry-After from response data."""
        config = RetryConfig()

        # Create exception with response data
        exc = MonzoRateLimitError("Rate limited")
        exc.response_data = {"retry_after": 45}

        assert config.get_retry_after(exc) == 45.0

    def test_get_retry_after_headers_priority(self) -> None:
        """Test that headers take priority over response data."""
        config = RetryConfig()

        # Create exception with both headers and response data
        exc = MonzoRateLimitError("Rate limited")
        exc.response_headers = {"retry-after": "10"}
        exc.response_data = {"retry_after": 20}

        assert config.get_retry_after(exc) == 10.0

    def test_get_retry_after_invalid_values(self) -> None:
        """Test handling of invalid Retry-After values."""
        config = RetryConfig()

        # Invalid header value
        exc = MonzoRateLimitError("Rate limited")
        exc.response_headers = {"retry-after": "invalid"}
        assert config.get_retry_after(exc) is None

        # Invalid response data value
        exc.response_data = {"retry_after": "also_invalid"}
        assert config.get_retry_after(exc) is None

    def test_get_retry_after_non_rate_limit_error(self) -> None:
        """Test get_retry_after with non-rate-limit exceptions."""
        config = RetryConfig()
        exc = MonzoServerError("Server error")

        assert config.get_retry_after(exc) is None


class TestWithRetryDecorator:
    """Test with_retry decorator."""

    def test_successful_function_no_retry(self) -> None:
        """Test that successful functions are not retried."""
        call_count = 0

        @with_retry()
        def successful_function() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_function_with_retryable_exception(self) -> None:
        """Test function that fails then succeeds."""
        call_count = 0

        @with_retry(RetryConfig(base_delay=0.01, jitter=False))
        def flaky_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                msg = "Rate limited"
                raise MonzoRateLimitError(msg)
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_function_exceeds_max_retries(self) -> None:
        """Test function that fails more than max retries."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=2, base_delay=0.01))
        def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            msg = "Always fails"
            raise MonzoRateLimitError(msg)

        with pytest.raises(MonzoRateLimitError):
            always_fails()
        assert call_count == 3  # Initial call + 2 retries

    def test_function_with_non_retryable_exception(self) -> None:
        """Test function with non-retryable exception."""
        call_count = 0

        @with_retry()
        def non_retryable_error() -> str:
            nonlocal call_count
            call_count += 1
            msg = "Not retryable"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Not retryable"):
            non_retryable_error()
        assert call_count == 1  # No retries

    def test_custom_retry_config(self) -> None:
        """Test with custom retry configuration."""
        call_count = 0
        config = RetryConfig(
            max_retries=1,
            retryable_exceptions=(MonzoServerError,),
            base_delay=0.01,
        )

        @with_retry(config)
        def custom_config_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                msg = "Server error"
                raise MonzoServerError(msg)
            return "success"

        result = custom_config_function()
        assert result == "success"
        assert call_count == 2

    @patch("time.sleep")
    def test_retry_delay_called(self, mock_sleep: Mock) -> None:
        """Test that retry delays are properly applied."""
        call_count = 0

        @with_retry(RetryConfig(base_delay=1.0, jitter=False))
        def delayed_retry() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                msg = "Rate limited"
                raise MonzoRateLimitError(msg)
            return "success"

        result = delayed_retry()
        assert result == "success"
        assert mock_sleep.call_count == 2
        # Check that delays increase exponentially
        mock_sleep.assert_any_call(1.0)  # First retry
        mock_sleep.assert_any_call(2.0)  # Second retry


class TestWithAsyncRetryDecorator:
    """Test with_async_retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_async_function_no_retry(self) -> None:
        """Test that successful async functions are not retried."""
        call_count = 0

        @with_async_retry()
        async def successful_function() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_function_with_retryable_exception(self) -> None:
        """Test async function that fails then succeeds."""
        call_count = 0

        @with_async_retry(RetryConfig(base_delay=0.01, jitter=False))
        async def flaky_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                msg = "Rate limited"
                raise MonzoRateLimitError(msg)
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_function_exceeds_max_retries(self) -> None:
        """Test async function that fails more than max retries."""
        call_count = 0

        @with_async_retry(RetryConfig(max_retries=2, base_delay=0.01))
        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            msg = "Always fails"
            raise MonzoRateLimitError(msg)

        with pytest.raises(MonzoRateLimitError):
            await always_fails()
        assert call_count == 3  # Initial call + 2 retries

    @pytest.mark.asyncio
    async def test_async_function_with_non_retryable_exception(self) -> None:
        """Test async function with non-retryable exception."""
        call_count = 0

        @with_async_retry()
        async def non_retryable_error() -> str:
            nonlocal call_count
            call_count += 1
            msg = "Not retryable"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Not retryable"):
            await non_retryable_error()
        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    @patch("asyncio.sleep")
    async def test_async_retry_delay_called(self, mock_sleep: Mock) -> None:
        """Test that async retry delays are properly applied."""
        call_count = 0
        mock_sleep.return_value = None  # asyncio.sleep returns None

        @with_async_retry(RetryConfig(base_delay=1.0, jitter=False))
        async def delayed_retry() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                msg = "Rate limited"
                raise MonzoRateLimitError(msg)
            return "success"

        result = await delayed_retry()
        assert result == "success"
        assert mock_sleep.call_count == 2
        # Check that delays increase exponentially
        mock_sleep.assert_any_call(1.0)  # First retry
        mock_sleep.assert_any_call(2.0)  # Second retry


class TestRetryWithRateLimitHeaders:
    """Test retry behavior with rate limit headers."""

    @patch("time.sleep")
    def test_retry_respects_retry_after_header(self, mock_sleep: Mock) -> None:
        """Test that retry respects Retry-After header."""
        call_count = 0

        @with_retry(RetryConfig(base_delay=10.0))  # High base delay
        def rate_limited_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                exc = MonzoRateLimitError("Rate limited")
                exc.response_headers = {"retry-after": "2"}
                raise exc
            return "success"

        result = rate_limited_function()
        assert result == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(2.0)  # Should use Retry-After value

    @pytest.mark.asyncio
    @patch("asyncio.sleep")
    async def test_async_retry_respects_retry_after_header(
        self, mock_sleep: Mock
    ) -> None:
        """Test that async retry respects Retry-After header."""
        call_count = 0
        mock_sleep.return_value = None

        @with_async_retry(RetryConfig(base_delay=10.0))  # High base delay
        async def rate_limited_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                exc = MonzoRateLimitError("Rate limited")
                exc.response_headers = {"retry-after": "3"}
                raise exc
            return "success"

        result = await rate_limited_function()
        assert result == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(3.0)  # Should use Retry-After value

    @patch("time.sleep")
    def test_retry_after_respects_max_delay(self, mock_sleep: Mock) -> None:
        """Test that Retry-After still respects max_delay."""
        call_count = 0

        @with_retry(RetryConfig(max_delay=5.0))
        def rate_limited_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                exc = MonzoRateLimitError("Rate limited")
                exc.response_headers = {"retry-after": "10"}  # Higher than max_delay
                raise exc
            return "success"

        result = rate_limited_function()
        assert result == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(5.0)  # Should be capped at max_delay
