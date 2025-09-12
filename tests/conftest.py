"""Test configuration and fixtures."""

from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from monzoh import AsyncMonzoClient, MonzoClient, MonzoOAuth
from monzoh.core.async_base import BaseAsyncClient


@pytest.fixture
def mock_response() -> Callable[..., Mock]:
    """Create a mock httpx response factory.

    Returns:
        A callable that creates mock httpx Response objects.
    """

    def create_response(
        status_code: int = 200, json_data: dict[str, Any] | None = None
    ) -> Mock:
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = str(json_data) if json_data else ""
        return response

    return create_response


@pytest.fixture
def mock_http_client(mock_response: Callable[..., Mock]) -> Mock:
    """Create a mock HTTP client.

    Args:
        mock_response: Mock response factory fixture.

    Returns:
        A mock HTTP client.
    """
    client = Mock(spec=httpx.Client)
    default_response = mock_response(200, {})
    client.request.return_value = default_response
    client.get.return_value = default_response
    client.post.return_value = default_response
    client.put.return_value = default_response
    client.patch.return_value = default_response
    client.delete.return_value = default_response
    client.close.return_value = None
    return client


@pytest.fixture
def monzo_client(
    mock_http_client: Mock, mock_response: Callable[..., Mock]
) -> MonzoClient:
    """Create a Monzo client with mocked HTTP client.

    Args:
        mock_http_client: Mock HTTP client fixture.
        mock_response: Mock response factory fixture.

    Returns:
        A MonzoClient instance with mocked dependencies.
    """
    client = MonzoClient(access_token="test_token", http_client=mock_http_client)
    default_response = mock_response()

    setattr(client._base_client, "_get", Mock(return_value=default_response))
    setattr(client._base_client, "_post", Mock(return_value=default_response))
    setattr(client._base_client, "_put", Mock(return_value=default_response))
    setattr(client._base_client, "_patch", Mock(return_value=default_response))
    setattr(client._base_client, "_delete", Mock(return_value=default_response))

    return client


@pytest.fixture
def oauth_client(mock_http_client: Mock) -> MonzoOAuth:
    """Create a Monzo OAuth client with mocked HTTP client.

    Args:
        mock_http_client: Mock HTTP client fixture.

    Returns:
        A MonzoOAuth instance with mocked dependencies.
    """
    return MonzoOAuth(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://example.com/callback",
        http_client=mock_http_client,
    )


@pytest.fixture
def sample_account() -> dict[str, Any]:
    """Sample account data.

    Returns:
        A dictionary containing sample account data.
    """
    return {
        "id": "acc_00009237aqC8c5umZmrRdh",
        "description": "Peter Pan's Account",
        "created": "2015-11-13T12:17:42Z",
    }


@pytest.fixture
def sample_balance() -> dict[str, Any]:
    """Sample balance data.

    Returns:
        A dictionary containing sample balance data.
    """
    return {
        "balance": 5000,
        "total_balance": 6000,
        "currency": "GBP",
        "spend_today": 0,
        "balance_including_flexible_savings": False,
        "local_currency": "GBP",
        "local_exchange_rate": 100,
        "local_spend": 0,
    }


@pytest.fixture
def sample_transaction() -> dict[str, Any]:
    """Sample transaction data.

    Returns:
        A dictionary containing sample transaction data.
    """
    return {
        "id": "tx_00008zIcpb1TB4yeIFXMzx",
        "amount": -510,
        "created": "2015-08-22T12:20:18Z",
        "currency": "GBP",
        "description": "THE DE BEAUVOIR DELI C LONDON        GBR",
        "merchant": "merch_00008zIcpbAKe8shBxXUtl",
        "metadata": {},
        "notes": "Salmon sandwich 🍞",
        "is_load": False,
        "settled": "2015-08-23T12:20:18Z",
        "category": "eating_out",
    }


@pytest.fixture
def sample_pot() -> dict[str, Any]:
    """Sample pot data.

    Returns:
        A dictionary containing sample pot data.
    """
    return {
        "id": "pot_0000778xxfgh4iu8z83nWb",
        "name": "Savings",
        "style": "beach_ball",
        "balance": 133700,
        "currency": "GBP",
        "created": "2017-11-09T12:30:53.695Z",
        "updated": "2017-11-09T12:30:53.695Z",
        "deleted": False,
    }


# Async fixtures
@pytest.fixture
def mock_async_response() -> Callable[..., Mock]:
    """Create a mock async response factory.

    Returns:
        A callable that creates mock async response objects.
    """

    def create_response(
        status_code: int = 200, json_data: dict[str, Any] | None = None
    ) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = str(json_data) if json_data else ""
        return response

    return create_response


@pytest.fixture
def mock_async_http_client(mock_async_response: Callable[..., Mock]) -> Mock:
    """Create a mock async HTTP client.

    Args:
        mock_async_response: Mock async response factory fixture.

    Returns:
        A mock async HTTP client.
    """
    client = Mock(spec=httpx.AsyncClient)
    default_response = mock_async_response(200, {})

    client.request = AsyncMock(return_value=default_response)
    client.get = AsyncMock(return_value=default_response)
    client.post = AsyncMock(return_value=default_response)
    client.put = AsyncMock(return_value=default_response)
    client.patch = AsyncMock(return_value=default_response)
    client.delete = AsyncMock(return_value=default_response)
    client.aclose = AsyncMock(return_value=None)

    return client


@pytest.fixture
def mock_async_base_client(mock_async_response: Callable[..., Mock]) -> Mock:
    """Create mock async base client.

    Args:
        mock_async_response: Mock async response factory fixture.

    Returns:
        A mock async base client.
    """
    client = Mock(spec=BaseAsyncClient)

    # Set up default response
    mock_response = mock_async_response()
    client._get = AsyncMock(return_value=mock_response)
    client._post = AsyncMock(return_value=mock_response)
    client._put = AsyncMock(return_value=mock_response)
    client._patch = AsyncMock(return_value=mock_response)
    client._delete = AsyncMock(return_value=mock_response)

    # Mock helper methods
    client._prepare_pagination_params = Mock(return_value={})
    client._prepare_expand_params = Mock(return_value=None)

    return client


@pytest.fixture
def async_monzo_client(
    mock_async_http_client: Mock, mock_async_response: Callable[..., Mock]
) -> AsyncMonzoClient:
    """Create an async Monzo client with mocked HTTP client.

    Args:
        mock_async_http_client: Mock async HTTP client fixture.
        mock_async_response: Mock async response factory fixture.

    Returns:
        An AsyncMonzoClient instance with mocked dependencies.
    """
    client = AsyncMonzoClient(
        access_token="test_token", http_client=mock_async_http_client
    )
    default_response = mock_async_response()

    # Mock the base client methods to return async mocks
    setattr(client._base_client, "_get", AsyncMock(return_value=default_response))
    setattr(client._base_client, "_post", AsyncMock(return_value=default_response))
    setattr(client._base_client, "_put", AsyncMock(return_value=default_response))
    setattr(client._base_client, "_patch", AsyncMock(return_value=default_response))
    setattr(client._base_client, "_delete", AsyncMock(return_value=default_response))

    return client
