"""Tests for synchronous functionality only."""

from typing import Any

import pytest

from monzoh import MonzoClient


class TestSync:
    """Test sync mode only (async mode no longer supported)."""

    def test_sync_mode_default(self) -> None:
        """Test sync mode is default and only mode."""
        client = MonzoClient("test_token")
        assert not client.async_mode
        assert hasattr(client._base_client, "__enter__")
        assert hasattr(client._base_client, "__exit__")

    def test_async_mode_raises_error(self) -> None:
        """Test async mode is no longer supported."""
        with pytest.raises(ValueError, match="Async mode is no longer supported"):
            MonzoClient("test_token", async_mode=True)

    def test_sync_context_manager(self, mock_sync_http_client: Any) -> None:
        """Test sync context manager."""
        with MonzoClient("test_token", http_client=mock_sync_http_client) as client:
            assert isinstance(client, MonzoClient)
            assert not client.async_mode

    def test_accounts_api_is_sync(
        self, mock_sync_http_client: Any, mock_httpx_response: Any
    ) -> None:
        """Test accounts API returns results synchronously."""
        client = MonzoClient("test_token", http_client=mock_sync_http_client)

        mock_response = mock_httpx_response(
            json_data={
                "accounts": [
                    {
                        "id": "acc_123",
                        "closed": False,
                        "created": "2020-01-01T00:00:00.000Z",
                        "description": "Test Account",
                        "type": "uk_retail",
                        "currency": "GBP",
                        "country_code": "GB",
                        "owners": [],
                        "account_number": "12345678",
                        "sort_code": "123456",
                    }
                ]
            }
        )
        mock_sync_http_client.request.return_value = mock_response

        # Should return result directly, not a coroutine
        accounts = client.accounts.list()
        assert len(accounts) == 1
        assert accounts[0].id == "acc_123"
