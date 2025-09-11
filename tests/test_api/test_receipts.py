"""Tests for receipts API."""

from typing import Any

from monzoh.api.receipts import ReceiptsAPI
from monzoh.models import Receipt, ReceiptItem


class TestReceiptsAPI:
    """Test ReceiptsAPI."""

    def test_init(self, monzo_client: Any) -> None:
        """Test client initialization.

        Args:
            monzo_client: Monzo client fixture.
        """
        api = ReceiptsAPI(monzo_client._base_client)
        assert api.client is monzo_client._base_client

    def test_create(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create receipt.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        response_data = {"receipt_id": "receipt_123"}
        mock_response = mock_response(json_data=response_data)
        monzo_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_client._base_client)
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
        monzo_client._base_client._put.assert_called_once()

    def test_create_no_receipt_id(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create receipt with no receipt_id returned.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        response_data: dict[str, Any] = {}
        mock_response = mock_response(json_data=response_data)
        monzo_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_client._base_client)
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
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create receipt with non-string receipt_id.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        response_data = {"receipt_id": 12345}
        mock_response = mock_response(json_data=response_data)
        monzo_client._base_client._put.return_value = mock_response

        api = ReceiptsAPI(monzo_client._base_client)
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
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test retrieve receipt.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
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
        mock_response = mock_response(json_data=response_data)
        monzo_client._base_client._get.return_value = mock_response

        api = ReceiptsAPI(monzo_client._base_client)
        result = api.retrieve("tx_00008zIcpb1TB4yeIFXMzx")

        assert isinstance(result, Receipt)
        assert result.external_id == "tx_00008zIcpb1TB4yeIFXMzx"
        assert result.total == 1000

    def test_delete(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test delete receipt.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response(json_data={})
        monzo_client._base_client._delete.return_value = mock_response

        api = ReceiptsAPI(monzo_client._base_client)
        api.delete("tx_00008zIcpb1TB4yeIFXMzx")
        monzo_client._base_client._delete.assert_called_once()
