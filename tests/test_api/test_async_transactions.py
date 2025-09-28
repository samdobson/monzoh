"""Tests for async transactions API."""

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock  # noqa: TC003

import pytest

from monzoh.api.async_transactions import AsyncTransactionsAPI
from monzoh.core.async_base import BaseAsyncClient

if TYPE_CHECKING:
    from monzoh.types import Metadata


class TestAsyncTransactionsAPI:
    """Test async transactions API."""

    @pytest.fixture
    def transactions_api(
        self, mock_async_base_client: BaseAsyncClient
    ) -> AsyncTransactionsAPI:
        """Create async transactions API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncTransactionsAPI instance.
        """
        return AsyncTransactionsAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_list_transactions(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test list transactions.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._get).return_value.json.return_value = {
            "transactions": [sample_transaction]
        }

        transactions = await transactions_api.list("test_account_id")

        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/transactions", params={"account_id": "test_account_id"}
        )
        assert len(transactions) == 1
        assert transactions[0].id == sample_transaction["id"]

    @pytest.mark.asyncio
    async def test_list_transactions_with_pagination(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test list transactions with pagination.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._get).return_value.json.return_value = {
            "transactions": [sample_transaction]
        }
        cast("Mock", mock_async_base_client._prepare_pagination_params).return_value = {
            "limit": "10",
            "since": "2023-01-01",
        }

        await transactions_api.list("test_account_id", limit=10, since="2023-01-01")

        expected_params = {
            "account_id": "test_account_id",
            "limit": "10",
            "since": "2023-01-01",
        }
        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/transactions", params=expected_params
        )

    @pytest.mark.asyncio
    async def test_list_transactions_with_expand(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test list transactions with expand.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._get).return_value.json.return_value = {
            "transactions": [sample_transaction]
        }
        cast("Mock", mock_async_base_client._prepare_expand_params).return_value = [
            ("expand[]", "merchant")
        ]
        cast(
            "Mock", mock_async_base_client._prepare_pagination_params
        ).return_value = {}

        await transactions_api.list("test_account_id", expand=["merchant"])

        expected_params = [("account_id", "test_account_id"), ("expand[]", "merchant")]
        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/transactions", params=expected_params
        )

    @pytest.mark.asyncio
    async def test_retrieve_transaction(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test retrieve single transaction.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._get).return_value.json.return_value = {
            "transaction": sample_transaction
        }
        cast("Mock", mock_async_base_client._prepare_expand_params).return_value = None

        transaction = await transactions_api.retrieve("test_transaction_id")

        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/transactions/test_transaction_id", params=None
        )
        assert transaction.id == sample_transaction["id"]

    @pytest.mark.asyncio
    async def test_annotate_transaction(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test annotate transaction.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._patch).return_value.json.return_value = {
            "transaction": sample_transaction
        }

        metadata: Metadata = {"category": "lunch", "notes": "Business meal"}
        transaction = await transactions_api.annotate("test_transaction_id", metadata)

        expected_data = {
            "metadata[category]": "lunch",
            "metadata[notes]": "Business meal",
        }
        cast("Mock", mock_async_base_client._patch).assert_called_once_with(
            "/transactions/test_transaction_id", data=expected_data
        )
        assert transaction.id == sample_transaction["id"]

    @pytest.mark.asyncio
    async def test_annotate_transaction_delete_metadata(
        self,
        transactions_api: AsyncTransactionsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_transaction: dict[str, Any],
    ) -> None:
        """Test annotate transaction with metadata deletion.

        Args:
            transactions_api: Async transactions API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_transaction: Sample transaction data fixture.
        """
        cast("Mock", mock_async_base_client._patch).return_value.json.return_value = {
            "transaction": sample_transaction
        }

        metadata: Metadata = {"category": ""}
        await transactions_api.annotate("test_transaction_id", metadata)

        expected_data = {"metadata[category]": ""}
        cast("Mock", mock_async_base_client._patch).assert_called_once_with(
            "/transactions/test_transaction_id", data=expected_data
        )
