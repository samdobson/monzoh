"""Tests for receipts API."""

from typing import Any

from monzoh.models import Receipt, ReceiptItem
from monzoh.receipts import ReceiptsAPI


class TestReceiptsAPI:
    """Test ReceiptsAPI."""

    def test_init(self, monzo_sync_client: Any) -> None:
        """Test client initialization."""
        api = ReceiptsAPI(monzo_sync_client._base_client)
        assert api.client is monzo_sync_client._base_client

    def test_create(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test create receipt."""
        response_data = {"receipt_id": "receipt_123"}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_sync_client._base_client)
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

        result = api.create(receipt)

        assert result == "receipt_123"
        monzo_sync_client._base_client._put.assert_called_once()

    def test_create_no_receipt_id(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test create receipt with no receipt_id returned."""
        response_data: dict[str, Any] = {}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_sync_client._base_client)
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

        result = api.create(receipt)

        assert result == ""

    def test_create_non_string_receipt_id(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test create receipt with non-string receipt_id."""
        response_data = {"receipt_id": 12345}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_sync_client._base_client)
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

        result = api.create(receipt)

        assert result == ""

    def test_retrieve(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test retrieve receipt."""
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
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._get.return_value = mock_response

        api = ReceiptsAPI(monzo_sync_client._base_client)
        result = api.retrieve("tx_00008zIcpb1TB4yeIFXMzx")

        assert isinstance(result, Receipt)
        assert result.external_id == "tx_00008zIcpb1TB4yeIFXMzx"
        assert result.total == 1000

    def test_delete(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test delete receipt."""
        mock_response = mock_httpx_response(json_data={})
        monzo_sync_client._base_client._delete.return_value = mock_response

        api = ReceiptsAPI(monzo_sync_client._base_client)
        api.delete("tx_00008zIcpb1TB4yeIFXMzx")
        monzo_sync_client._base_client._delete.assert_called_once()
