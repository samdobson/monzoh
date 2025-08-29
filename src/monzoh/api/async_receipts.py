"""Async receipts API endpoints."""

from ..core.async_base import BaseAsyncClient
from ..models import Receipt, ReceiptResponse


class AsyncReceiptsAPI:
    """Async receipts API client."""

    def __init__(self, client: BaseAsyncClient) -> None:
        """Initialize async receipts API.

        Args:
            client: Base async API client
        """
        self.client = client

    async def create(self, receipt: Receipt) -> str:
        """Create or update a receipt.

        Args:
            receipt: Receipt data

        Returns:
            Receipt ID
        """
        # Convert receipt to dict, excluding None values
        receipt_dict = receipt.model_dump(exclude_none=True)

        response = await self.client._put(
            "/transaction-receipts",
            json_data=receipt_dict,
            headers={"Content-Type": "application/json"},
        )

        # The API returns the receipt with an ID
        response_data = response.json()
        receipt_id = response_data.get("receipt_id")
        return receipt_id if isinstance(receipt_id, str) else ""

    async def retrieve(self, external_id: str) -> Receipt:
        """Retrieve a receipt by external ID.

        Args:
            external_id: External ID of the receipt

        Returns:
            Receipt data
        """
        params = {"external_id": external_id}

        response = await self.client._get("/transaction-receipts", params=params)
        receipt_response = ReceiptResponse(**response.json())
        return receipt_response.receipt

    async def delete(self, external_id: str) -> None:
        """Delete a receipt by external ID.

        Args:
            external_id: External ID of the receipt

        Returns:
            None
        """
        params = {"external_id": external_id}

        await self.client._delete("/transaction-receipts", params=params)
