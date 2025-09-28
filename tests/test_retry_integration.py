"""Integration tests for retry functionality with HTTP clients."""

from unittest.mock import Mock, patch

import httpx
import pytest

from monzoh.core.async_base import BaseAsyncClient
from monzoh.core.base import BaseSyncClient
from monzoh.core.retry import RetryConfig
from monzoh.exceptions import (
    MonzoAuthenticationError,
    MonzoRateLimitError,
    MonzoServerError,
)


class TestSyncClientRetryIntegration:
    """Test retry integration with sync HTTP client."""

    def test_sync_client_retry_on_rate_limit(self) -> None:
        """Test sync client retries on rate limit errors."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count <= 2:
                # First two calls return rate limit error
                mock_response.status_code = 429
                mock_response.text = "Rate limit exceeded"
                mock_response.json.return_value = {"error": "rate_limit_exceeded"}
                mock_response.headers = {"retry-after": "1"}
            else:
                # Third call succeeds
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=3, base_delay=0.01)
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("time.sleep"):  # Speed up tests
            response = client._get("/test")

        assert response.status_code == 200
        assert call_count == 3  # Should have made 3 attempts

    def test_sync_client_retry_on_server_error(self) -> None:
        """Test sync client retries on server errors."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count == 1:
                # First call returns server error
                mock_response.status_code = 500
                mock_response.text = "Internal server error"
                mock_response.json.return_value = {"error": "internal_error"}
                mock_response.headers = {}
            else:
                # Second call succeeds
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=2, base_delay=0.01)
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("time.sleep"):  # Speed up tests
            response = client._get("/test")

        assert response.status_code == 200
        assert call_count == 2  # Should have made 2 attempts

    def test_sync_client_retry_on_network_error(self) -> None:
        """Test sync client retries on network errors."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First two calls raise network error
                msg = "Connection failed"
                raise httpx.RequestError(msg)
            # Third call succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.headers = {}
            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=3, base_delay=0.01)
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("time.sleep"):  # Speed up tests
            response = client._get("/test")

        assert response.status_code == 200
        assert call_count == 3  # Should have made 3 attempts

    def test_sync_client_exceeds_max_retries(self) -> None:
        """Test sync client when max retries are exceeded."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.json.return_value = {"error": "rate_limit_exceeded"}
            mock_response.headers = {}
            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=2, base_delay=0.01)
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with (
            patch("time.sleep"),  # Speed up tests
            pytest.raises(MonzoRateLimitError),
        ):
            client._get("/test")

        assert call_count == 3  # Initial call + 2 retries

    def test_sync_client_no_retry_on_auth_error(self) -> None:
        """Test sync client doesn't retry on authentication errors."""
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.json.return_value = {"error": "unauthorized"}
        mock_response.headers = {}
        mock_http_client.request.return_value = mock_response

        retry_config = RetryConfig(max_retries=3, base_delay=0.01)
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with pytest.raises(MonzoAuthenticationError):
            client._get("/test")

        assert mock_http_client.request.call_count == 1  # No retries

    def test_sync_client_respects_retry_after_header(self) -> None:
        """Test sync client respects Retry-After header."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count == 1:
                mock_response.status_code = 429
                mock_response.text = "Rate limit exceeded"
                mock_response.json.return_value = {"error": "rate_limit_exceeded"}
                mock_response.headers = {"retry-after": "5"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(base_delay=1.0)  # Lower than retry-after
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("time.sleep") as mock_sleep:
            response = client._get("/test")

        assert response.status_code == 200
        assert call_count == 2
        mock_sleep.assert_called_once_with(5.0)  # Should use Retry-After value

    def test_sync_client_custom_retry_config(self) -> None:
        """Test sync client with custom retry configuration."""
        mock_http_client = Mock()
        call_count = 0

        def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count <= 1:
                # Only retry server errors, not rate limits
                mock_response.status_code = 500
                mock_response.text = "Server error"
                mock_response.json.return_value = {"error": "server_error"}
                mock_response.headers = {}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        # Custom config that only retries server errors
        retry_config = RetryConfig(
            max_retries=1, retryable_exceptions=(MonzoServerError,), base_delay=0.01
        )
        client = BaseSyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("time.sleep"):
            response = client._get("/test")

        assert response.status_code == 200
        assert call_count == 2


class TestAsyncClientRetryIntegration:
    """Test retry integration with async HTTP client."""

    @pytest.mark.asyncio
    async def test_async_client_retry_on_rate_limit(self) -> None:
        """Test async client retries on rate limit errors."""
        mock_http_client = Mock()
        call_count = 0

        async def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count <= 2:
                # First two calls return rate limit error
                mock_response.status_code = 429
                mock_response.text = "Rate limit exceeded"
                mock_response.json.return_value = {"error": "rate_limit_exceeded"}
                mock_response.headers = {"retry-after": "1"}
            else:
                # Third call succeeds
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=3, base_delay=0.01)
        client = BaseAsyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("asyncio.sleep"):  # Speed up tests
            response = await client._get("/test")

        assert response.status_code == 200
        assert call_count == 3  # Should have made 3 attempts

    @pytest.mark.asyncio
    async def test_async_client_retry_on_server_error(self) -> None:
        """Test async client retries on server errors."""
        mock_http_client = Mock()
        call_count = 0

        async def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count == 1:
                # First call returns server error
                mock_response.status_code = 500
                mock_response.text = "Internal server error"
                mock_response.json.return_value = {"error": "internal_error"}
                mock_response.headers = {}
            else:
                # Second call succeeds
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=2, base_delay=0.01)
        client = BaseAsyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("asyncio.sleep"):  # Speed up tests
            response = await client._get("/test")

        assert response.status_code == 200
        assert call_count == 2  # Should have made 2 attempts

    @pytest.mark.asyncio
    async def test_async_client_retry_on_network_error(self) -> None:
        """Test async client retries on network errors."""
        mock_http_client = Mock()
        call_count = 0

        async def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                # First two calls raise network error
                msg = "Connection failed"
                raise httpx.RequestError(msg)
            # Third call succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.headers = {}
            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=3, base_delay=0.01)
        client = BaseAsyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("asyncio.sleep"):  # Speed up tests
            response = await client._get("/test")

        assert response.status_code == 200
        assert call_count == 3  # Should have made 3 attempts

    @pytest.mark.asyncio
    async def test_async_client_exceeds_max_retries(self) -> None:
        """Test async client when max retries are exceeded."""
        mock_http_client = Mock()
        call_count = 0

        async def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.json.return_value = {"error": "rate_limit_exceeded"}
            mock_response.headers = {}
            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(max_retries=2, base_delay=0.01)
        client = BaseAsyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with (
            patch("asyncio.sleep"),  # Speed up tests
            pytest.raises(MonzoRateLimitError),
        ):
            await client._get("/test")

        assert call_count == 3  # Initial call + 2 retries

    @pytest.mark.asyncio
    async def test_async_client_respects_retry_after_header(self) -> None:
        """Test async client respects Retry-After header."""
        mock_http_client = Mock()
        call_count = 0

        async def side_effect(*_args, **_kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1

            mock_response = Mock()
            if call_count == 1:
                mock_response.status_code = 429
                mock_response.text = "Rate limit exceeded"
                mock_response.json.return_value = {"error": "rate_limit_exceeded"}
                mock_response.headers = {"retry-after": "3"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

            return mock_response

        mock_http_client.request.side_effect = side_effect

        retry_config = RetryConfig(base_delay=1.0)  # Lower than retry-after
        client = BaseAsyncClient(
            "test_token", mock_http_client, retry_config=retry_config
        )

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            response = await client._get("/test")

        assert response.status_code == 200
        assert call_count == 2
        mock_sleep.assert_called_once_with(3.0)  # Should use Retry-After value

    @pytest.mark.asyncio
    async def test_async_client_mock_mode_no_retry(self) -> None:
        """Test that mock mode doesn't apply retry logic."""
        # In mock mode, the client should not apply retry logic
        client = BaseAsyncClient("test")  # "test" token puts client in mock mode

        # Mock mode should return immediately without retry logic
        response = await client._get("/ping/whoami")

        # Should get a mock response
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


class TestRetryConfigIntegration:
    """Test RetryConfig integration with clients."""

    def test_client_uses_default_retry_config(self) -> None:
        """Test that client uses default retry config when none provided."""
        client = BaseSyncClient("test_token")

        assert client.retry_config is not None
        assert client.retry_config.max_retries == 3
        assert client.retry_config.base_delay == 1.0

    def test_client_uses_custom_retry_config(self) -> None:
        """Test that client uses custom retry config when provided."""
        custom_config = RetryConfig(max_retries=5, base_delay=2.0)
        client = BaseSyncClient("test_token", retry_config=custom_config)

        assert client.retry_config is custom_config
        assert client.retry_config.max_retries == 5
        assert client.retry_config.base_delay == 2.0

    def test_async_client_uses_default_retry_config(self) -> None:
        """Test that async client uses default retry config when none provided."""
        client = BaseAsyncClient("test_token")

        assert client.retry_config is not None
        assert client.retry_config.max_retries == 3
        assert client.retry_config.base_delay == 1.0

    def test_async_client_uses_custom_retry_config(self) -> None:
        """Test that async client uses custom retry config when provided."""
        custom_config = RetryConfig(max_retries=5, base_delay=2.0)
        client = BaseAsyncClient("test_token", retry_config=custom_config)

        assert client.retry_config is custom_config
        assert client.retry_config.max_retries == 5
        assert client.retry_config.base_delay == 2.0
