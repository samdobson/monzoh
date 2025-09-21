"""Tests for async base client."""

from unittest.mock import AsyncMock

import pytest

from monzoh.core.async_base import AsyncMockResponse, BaseAsyncClient


class TestAsyncMockResponse:
    """Test MockAsyncResponse class."""

    def test_async_mock_response_json(self) -> None:
        """Test AsyncMockResponse json method."""
        data = {"test": "data"}
        response = AsyncMockResponse(data, 200)

        assert response.json() == data

    def test_async_mock_response_raise_for_status_success(self) -> None:
        """Test AsyncMockResponse raise_for_status with success status."""
        response = AsyncMockResponse({}, 200)
        response.raise_for_status()

    def test_async_mock_response_raise_for_status_error(self) -> None:
        """Test AsyncMockResponse raise_for_status with error status."""
        response = AsyncMockResponse({}, 400)

        with pytest.raises(Exception, match="HTTP 400 error"):
            response.raise_for_status()

    def test_async_mock_response_raise_for_status_server_error(self) -> None:
        """Test AsyncMockResponse raise_for_status with server error."""
        response = AsyncMockResponse({}, 500)

        with pytest.raises(Exception, match="HTTP 500 error"):
            response.raise_for_status()


class TestBaseAsyncClient:
    """Test BaseAsyncClient class."""

    @pytest.mark.asyncio
    async def test_aexit_with_own_client(self) -> None:
        """Test __aexit__ when we own the HTTP client."""
        client = BaseAsyncClient(access_token="test_token")
        client._own_client = True
        client._http_client = AsyncMock()

        await client.__aexit__(None, None, None)

        client._http_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_aexit_without_own_client(self) -> None:
        """Test __aexit__ when we don't own the HTTP client."""
        client = BaseAsyncClient(access_token="test_token")
        client._own_client = False
        client._http_client = AsyncMock()

        await client.__aexit__(None, None, None)

        client._http_client.aclose.assert_not_called()

    @pytest.mark.asyncio
    async def test_aexit_no_http_client(self) -> None:
        """Test __aexit__ when there's no HTTP client."""
        client = BaseAsyncClient(access_token="test_token")
        client._own_client = True
        client._http_client = None

        await client.__aexit__(None, None, None)
