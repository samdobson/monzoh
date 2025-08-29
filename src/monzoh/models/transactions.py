"""Transaction-related models."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from ..core import BaseSyncClient
    from .attachments import Attachment


class Address(BaseModel):
    """Address information."""

    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code (e.g., 'GB')")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    postcode: str = Field(..., description="Postal code")
    region: str = Field(..., description="Region or county name")


class Merchant(BaseModel):
    """Merchant information."""

    id: str = Field(..., description="Unique merchant identifier")
    name: str = Field(..., description="Merchant display name")
    category: str = Field(
        ..., description="Merchant category (e.g., 'eating_out', 'transport')"
    )
    created: datetime = Field(..., description="Merchant creation timestamp")
    group_id: str = Field(..., description="Merchant group identifier")
    logo: str | None = Field(None, description="URL to merchant logo image")
    emoji: str | None = Field(None, description="Emoji representing the merchant")
    address: Address | None = Field(None, description="Merchant address information")


class Transaction(BaseModel):
    """Represents a transaction."""

    id: str = Field(..., description="Unique transaction identifier")
    amount: int = Field(
        ...,
        description=(
            "Amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD (negative for debits)"
        ),
    )
    created: datetime = Field(..., description="Transaction creation timestamp")
    currency: str = Field(..., description="ISO 4217 currency code (e.g., 'GBP')")
    description: str = Field(
        ..., description="Transaction description from payment processor"
    )
    account_balance: int | None = Field(
        None,
        description=(
            "Account balance after transaction in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    category: str | None = Field(
        None,
        description=(
            "Transaction category (e.g., 'eating_out', 'transport', 'groceries')"
        ),
    )
    is_load: bool = Field(False, description="Whether this is a top-up transaction")
    settled: datetime | None = Field(
        None, description="Settlement timestamp (when transaction completed)"
    )
    merchant: str | Merchant | None = Field(
        None, description="Merchant ID or expanded merchant object"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom key-value metadata"
    )
    notes: str | None = Field(None, description="User-added notes for the transaction")
    decline_reason: (
        Literal[
            "INSUFFICIENT_FUNDS",
            "CARD_INACTIVE",
            "CARD_BLOCKED",
            "INVALID_CVC",
            "OTHER",
            "STRONG_CUSTOMER_AUTHENTICATION_REQUIRED",
        ]
        | None
    ) = Field(
        None,
        description=(
            "Reason for transaction decline (only present on declined transactions)"
        ),
    )

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._client: BaseSyncClient | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to set up client if available."""
        super().model_post_init(__context)

    def _ensure_client(self) -> BaseSyncClient:
        """Ensure client is available for API calls."""
        if self._client is None:
            raise RuntimeError(
                "No client available. Transaction must be retrieved from MonzoClient "
                "to use methods."
            )
        return self._client

    def _set_client(self, client: BaseSyncClient) -> Transaction:
        """Set the client for this transaction instance."""
        self._client = client
        return self

    def upload_attachment(
        self,
        file_path: str | Path,
        file_name: str | None = None,
        file_type: str | None = None,
    ) -> Attachment:
        """Upload and attach a file to this transaction.

        Args:
            file_path: Path to the file to upload
            file_name: Custom name for the file (defaults to filename from path)
            file_type: MIME type (inferred from file extension if not provided)

        Returns:
            The uploaded attachment

        Raises:
            RuntimeError: If no client is available (transaction not retrieved from API)
        """
        client = self._ensure_client()
        from ..api.attachments import AttachmentsAPI

        attachments_api = AttachmentsAPI(client)
        return attachments_api.upload(
            transaction_id=self.id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
        )

    @field_validator("settled", mode="before")
    @classmethod
    def validate_settled(cls, v: str | None) -> str | None:
        """Convert empty strings to None for settled field."""
        if v == "":
            return None
        return v


# Response containers
class TransactionsResponse(BaseModel):
    """Transactions list response."""

    transactions: list[Transaction] = Field(..., description="List of transactions")


class TransactionResponse(BaseModel):
    """Single transaction response."""

    transaction: Transaction = Field(..., description="Single transaction object")
