"""Tests for async accounts API."""

from typing import Any, cast
from unittest.mock import Mock

import pytest

from monzoh.api.async_accounts import AsyncAccountsAPI
from monzoh.core.async_base import BaseAsyncClient


class TestAsyncAccountsAPI:
    """Test async accounts API."""

    @pytest.fixture
    def accounts_api(self, mock_async_base_client: BaseAsyncClient) -> AsyncAccountsAPI:
        """Create async accounts API instance."""
        return AsyncAccountsAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_list_accounts(
        self,
        accounts_api: AsyncAccountsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_account: dict[str, Any],
    ) -> None:
        """Test list accounts."""
        cast(Mock, mock_async_base_client._get).return_value.json.return_value = {
            "accounts": [sample_account]
        }

        accounts = await accounts_api.list()

        cast(Mock, mock_async_base_client._get).assert_called_once_with(
            "/accounts", params={}
        )
        assert len(accounts) == 1
        assert accounts[0].id == sample_account["id"]

    @pytest.mark.asyncio
    async def test_list_accounts_with_filter(
        self,
        accounts_api: AsyncAccountsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_account: dict[str, Any],
    ) -> None:
        """Test list accounts with type filter."""
        cast(Mock, mock_async_base_client._get).return_value.json.return_value = {
            "accounts": [sample_account]
        }

        accounts = await accounts_api.list(account_type="uk_retail")

        cast(Mock, mock_async_base_client._get).assert_called_once_with(
            "/accounts", params={"account_type": "uk_retail"}
        )
        assert len(accounts) == 1

    @pytest.mark.asyncio
    async def test_get_balance(
        self,
        accounts_api: AsyncAccountsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_balance: dict[str, Any],
    ) -> None:
        """Test get account balance."""
        cast(Mock, mock_async_base_client._get).return_value.json.return_value = (
            sample_balance
        )

        balance = await accounts_api.get_balance("test_account_id")

        cast(Mock, mock_async_base_client._get).assert_called_once_with(
            "/balance", params={"account_id": "test_account_id"}
        )
        assert balance.balance == sample_balance["balance"]
        assert balance.currency == sample_balance["currency"]
