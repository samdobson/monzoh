"""Tests for async receipts API."""

from typing import Any, cast
from unittest.mock import Mock

import pytest

from monzoh.api.async_receipts import AsyncReceiptsAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Receipt, ReceiptItem


class TestAsyncReceiptsAPI:
    """Test async receipts API."""

    @pytest.fixture
    def receipts_api(self, mock_async_base_client: BaseAsyncClient) -> AsyncReceiptsAPI:
        """Create async receipts API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncReceiptsAPI instance.
        """
        return AsyncReceiptsAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_create(
        self,
        receipts_api: AsyncReceiptsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create receipt.

        Args:
            receipts_api: Async receipts API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        response_data = {"receipt_id": "receipt_123"}
        cast(
            "Mock", mock_async_base_client._put
        ).return_value.json.return_value = response_data

        receipt = Receipt(
            id=None,
            external_id="tx_00008zIcpb1TB4yeIFXMzx",
            transaction_id="tx_00008zIcpb1TB4yeIFXMzx",
            total=1000,
            currency="GBP",
            items=[
                ReceiptItem(
                    description="Coffee",
                    amount=250,
                    currency="GBP",
                    quantity=1,
                    unit=None,
                    tax=None,
                    sub_items=None,
                ),
                ReceiptItem(
                    description="Cake",
                    amount=750,
                    currency="GBP",
                    quantity=1,
                    unit=None,
                    tax=None,
                    sub_items=None,
                ),
            ],
            taxes=None,
            payments=None,
            merchant=None,
        )

        result = await receipts_api.create(receipt)

        assert result == "receipt_123"
        cast("Mock", mock_async_base_client._put).assert_called_once_with(
            "/transaction-receipts",
            json_data=receipt.model_dump(exclude_none=True),
            headers={"Content-Type": "application/json"},
        )

    @pytest.mark.asyncio
    async def test_create_no_receipt_id(
        self,
        receipts_api: AsyncReceiptsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create receipt with no receipt_id returned.

        Args:
            receipts_api: Async receipts API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        response_data: dict[str, Any] = {}
        cast(
            "Mock", mock_async_base_client._put
        ).return_value.json.return_value = response_data

        receipt = Receipt(
            id=None,
            external_id="tx_00008zIcpb1TB4yeIFXMzx",
            transaction_id="tx_00008zIcpb1TB4yeIFXMzx",
            total=1000,
            currency="GBP",
            items=[],
            taxes=None,
            payments=None,
            merchant=None,
        )

        result = await receipts_api.create(receipt)

        assert result == ""

    @pytest.mark.asyncio
    async def test_create_non_string_receipt_id(
        self,
        receipts_api: AsyncReceiptsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create receipt with non-string receipt_id.

        Args:
            receipts_api: Async receipts API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        response_data = {"receipt_id": 12345}
        cast(
            "Mock", mock_async_base_client._put
        ).return_value.json.return_value = response_data

        receipt = Receipt(
            id=None,
            external_id="tx_00008zIcpb1TB4yeIFXMzx",
            transaction_id="tx_00008zIcpb1TB4yeIFXMzx",
            total=1000,
            currency="GBP",
            items=[],
            taxes=None,
            payments=None,
            merchant=None,
        )

        result = await receipts_api.create(receipt)

        assert result == ""

    @pytest.mark.asyncio
    async def test_retrieve(
        self,
        receipts_api: AsyncReceiptsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test retrieve receipt.

        Args:
            receipts_api: Async receipts API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        receipt_data = {
            "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "transaction_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "total": 1000,
            "currency": "GBP",
            "items": [
                {
                    "description": "Coffee",
                    "amount": 250,
                    "currency": "GBP",
                    "quantity": 1,
                }
            ],
        }
        response_data = {"receipt": receipt_data}
        cast(
            "Mock", mock_async_base_client._get
        ).return_value.json.return_value = response_data

        result = await receipts_api.retrieve("tx_00008zIcpb1TB4yeIFXMzx")

        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/transaction-receipts", params={"external_id": "tx_00008zIcpb1TB4yeIFXMzx"}
        )
        assert isinstance(result, Receipt)
        assert result.external_id == "tx_00008zIcpb1TB4yeIFXMzx"
        assert result.total == 1000

    @pytest.mark.asyncio
    async def test_delete(
        self,
        receipts_api: AsyncReceiptsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test delete receipt.

        Args:
            receipts_api: Async receipts API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        await receipts_api.delete("tx_00008zIcpb1TB4yeIFXMzx")

        cast("Mock", mock_async_base_client._delete).assert_called_once_with(
            "/transaction-receipts", params={"external_id": "tx_00008zIcpb1TB4yeIFXMzx"}
        )
