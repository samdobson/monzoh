"""Test configuration and fixtures."""

from typing import Any, Callable, Optional
from unittest.mock import Mock

import httpx
import pytest

from monzoh import MonzoClient, MonzoOAuth


@pytest.fixture
def mock_response() -> Callable[..., Mock]:
    """Create a mock httpx response factory."""

    def create_response(
        status_code: int = 200, json_data: Optional[dict[str, Any]] = None
    ) -> Mock:
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.text = str(json_data) if json_data else ""
        return response

    return create_response


@pytest.fixture
def mock_http_client(mock_response: Callable[..., Mock]) -> Mock:
    """Create a mock HTTP client."""
    client = Mock(spec=httpx.Client)
    default_response = mock_response()
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
    """Create a Monzo client with mocked HTTP client."""
    client = MonzoClient(access_token="test_token", http_client=mock_http_client)
    default_response = mock_response()
    # Type: ignore for method assignment to mock
    client._base_client._get = Mock(return_value=default_response)  # type: ignore
    client._base_client._post = Mock(return_value=default_response)  # type: ignore
    client._base_client._put = Mock(return_value=default_response)  # type: ignore
    client._base_client._patch = Mock(return_value=default_response)  # type: ignore
    client._base_client._delete = Mock(return_value=default_response)  # type: ignore
    return client


@pytest.fixture
def oauth_client(mock_http_client: Mock) -> MonzoOAuth:
    """Create a Monzo OAuth client with mocked HTTP client."""
    return MonzoOAuth(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="https://example.com/callback",
        http_client=mock_http_client,
    )


@pytest.fixture
def sample_account() -> dict[str, Any]:
    """Sample account data."""
    return {
        "id": "acc_00009237aqC8c5umZmrRdh",
        "description": "Peter Pan's Account",
        "created": "2015-11-13T12:17:42Z",
    }


@pytest.fixture
def sample_balance() -> dict[str, Any]:
    """Sample balance data."""
    return {"balance": 5000, "total_balance": 6000, "currency": "GBP", "spend_today": 0}


@pytest.fixture
def sample_transaction() -> dict[str, Any]:
    """Sample transaction data."""
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
    """Sample pot data."""
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
