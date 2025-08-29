"""Tests for the async client."""

from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from monzoh import AsyncMonzoClient, MonzoOAuth
from monzoh.core.async_base import AsyncMockResponse, BaseAsyncClient
from monzoh.exceptions import MonzoBadRequestError, MonzoNetworkError


class TestAsyncMonzoClient:
    """Test AsyncMonzoClient."""

    def test_init(self, mock_async_http_client: Any) -> None:
        """Test client initialization."""
        client = AsyncMonzoClient("test_token", http_client=mock_async_http_client)
        assert client._base_client.access_token == "test_token"
        assert client._base_client._http_client is mock_async_http_client

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_async_http_client: Any) -> None:
        """Test async context manager."""
        async with AsyncMonzoClient(
            "test_token", http_client=mock_async_http_client
        ) as client:
            assert isinstance(client, AsyncMonzoClient)

    @pytest.mark.asyncio
    async def test_whoami(
        self,
        async_monzo_client: Any,
        mock_async_http_client: Any,
        mock_async_response: Any,
    ) -> None:
        """Test whoami endpoint."""
        mock_response = mock_async_response(
            json_data={
                "authenticated": True,
                "client_id": "test_client_id",
                "user_id": "test_user_id",
            }
        )
        async_monzo_client._base_client._get.return_value = mock_response

        result = await async_monzo_client.whoami()

        assert result.authenticated is True
        assert result.client_id == "test_client_id"
        assert result.user_id == "test_user_id"

    def test_create_oauth_client(self, mock_async_http_client: Any) -> None:
        """Test OAuth client creation."""
        oauth_client = AsyncMonzoClient.create_oauth_client(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_async_http_client,
        )

        assert isinstance(oauth_client, MonzoOAuth)
        assert oauth_client.client_id == "test_id"
        assert oauth_client.client_secret == "test_secret"

    @pytest.mark.asyncio
    async def test_token_loading_from_cache(self, mock_async_http_client: Any) -> None:
        """Test loading token from cache."""
        with patch("monzoh.async_client._load_cached_token") as mock_load:
            mock_load.return_value = "cached_token"

            client = AsyncMonzoClient(http_client=mock_async_http_client)
            assert client._base_client.access_token == "cached_token"

    @pytest.mark.asyncio
    async def test_init_without_token_raises_error(
        self, mock_async_http_client: Any
    ) -> None:
        """Test initialization without token raises error."""
        with patch("monzoh.async_client._load_cached_token") as mock_load:
            mock_load.return_value = None

            with pytest.raises(Exception):
                AsyncMonzoClient(http_client=mock_async_http_client)

    @pytest.mark.asyncio
    async def test_api_endpoints_initialized(self, mock_async_http_client: Any) -> None:
        """Test that all API endpoints are initialized."""
        client = AsyncMonzoClient("test_token", http_client=mock_async_http_client)

        # Check that all async API endpoints are initialized
        assert hasattr(client, "accounts")
        assert hasattr(client, "transactions")
        assert hasattr(client, "pots")
        assert hasattr(client, "attachments")
        assert hasattr(client, "feed")
        assert hasattr(client, "receipts")
        assert hasattr(client, "webhooks")

        # Verify they are the async versions
        assert client.accounts.__class__.__name__ == "AsyncAccountsAPI"
        assert client.transactions.__class__.__name__ == "AsyncTransactionsAPI"
        assert client.pots.__class__.__name__ == "AsyncPotsAPI"
        assert client.attachments.__class__.__name__ == "AsyncAttachmentsAPI"
        assert client.feed.__class__.__name__ == "AsyncFeedAPI"
        assert client.receipts.__class__.__name__ == "AsyncReceiptsAPI"
        assert client.webhooks.__class__.__name__ == "AsyncWebhooksAPI"


class TestBaseAsyncClient:
    """Test BaseAsyncClient."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager for base client."""
        client = BaseAsyncClient(access_token="test_token")

        async with client:
            assert isinstance(client, BaseAsyncClient)

    @pytest.mark.asyncio
    async def test_mock_mode(self) -> None:
        """Test mock mode functionality."""
        client = BaseAsyncClient(access_token="test")
        assert client.is_mock_mode is True

        client = BaseAsyncClient(access_token="real_token")
        assert client.is_mock_mode is False

    @pytest.mark.asyncio
    async def test_mock_response_in_mock_mode(self) -> None:
        """Test that mock responses are returned in mock mode."""
        client = BaseAsyncClient(access_token="test")

        response = await client._get("/ping/whoami")
        assert isinstance(response, AsyncMockResponse)
        assert response.status_code == 200

    def test_auth_headers(self) -> None:
        """Test authorization headers generation."""
        client = BaseAsyncClient(access_token="test_token")
        headers = client.auth_headers
        assert headers == {"Authorization": "Bearer test_token"}

    @pytest.mark.asyncio
    async def test_http_client_creation(self) -> None:
        """Test HTTP client creation."""
        client = BaseAsyncClient(access_token="test_token")
        http_client = client.http_client

        assert isinstance(http_client, httpx.AsyncClient)
        assert "User-Agent" in http_client.headers
        assert "monzoh-python-client" in str(http_client.headers["User-Agent"])

    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_async_http_client: Any) -> None:
        """Test network error handling."""
        mock_async_http_client.request.side_effect = httpx.RequestError("Network error")

        client = BaseAsyncClient(
            access_token="test_token", http_client=mock_async_http_client
        )

        with pytest.raises(MonzoNetworkError):
            await client._request("GET", "/test")

    @pytest.mark.asyncio
    async def test_http_error_handling(self, mock_async_http_client: Any) -> None:
        """Test HTTP error handling."""
        error_response = Mock(spec=httpx.Response)
        error_response.status_code = 400
        error_response.text = "Bad request"
        error_response.json.return_value = {"error": "invalid_request"}

        mock_async_http_client.request.return_value = error_response

        client = BaseAsyncClient(
            access_token="test_token", http_client=mock_async_http_client
        )

        with pytest.raises(MonzoBadRequestError):
            await client._request("GET", "/test")

    def test_pagination_params(self) -> None:
        """Test pagination parameter preparation."""
        client = BaseAsyncClient(access_token="test_token")

        params = client._prepare_pagination_params(limit=10, since="2023-01-01")
        assert params == {"limit": "10", "since": "2023-01-01"}

    def test_expand_params(self) -> None:
        """Test expand parameter preparation."""
        client = BaseAsyncClient(access_token="test_token")

        params = client._prepare_expand_params(["merchant", "category"])
        assert params == [("expand[]", "merchant"), ("expand[]", "category")]

        # Test empty expand
        params = client._prepare_expand_params(None)
        assert params is None
