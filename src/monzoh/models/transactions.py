"""Transaction-related models."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from ..core import BaseSyncClient
    from ..core.async_base import BaseAsyncClient
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
    formatted: str | None = Field(None, description="Formatted address")
    short_formatted: str | None = Field(None, description="Short formatted address")
    zoom_level: int | None = Field(None, description="Map zoom level")
    approximate: bool | None = Field(None, description="Whether address is approximate")


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
    online: bool | None = Field(None, description="Whether merchant is online")
    atm: bool | None = Field(None, description="Whether merchant is an ATM")
    disable_feedback: bool | None = Field(
        None, description="Whether feedback is disabled"
    )
    metadata: dict[str, Any] | None = Field(None, description="Merchant metadata")
    suggested_tags: list[str] | None = Field(None, description="Suggested tags")


class Counterparty(BaseModel):
    """Counterparty information."""

    user_id: str | None = Field(None, description="User identifier")
    name: str | None = Field(None, description="Counterparty name")
    preferred_name: str | None = Field(None, description="Preferred name")
    sort_code: str | None = Field(None, description="Sort code")
    account_number: str | None = Field(None, description="Account number")


class Transaction(BaseModel):
    """Represents a transaction.

    Args:
        **data: Transaction data fields

    Attributes:
        id: Unique transaction identifier
        amount: Amount in minor units of the currency (negative for debits)
        created: Transaction creation timestamp
        currency: ISO 4217 currency code (e.g., 'GBP')
        description: Transaction description from payment processor
        account_balance: Account balance after transaction in minor units (optional)
        category: Transaction category (e.g., 'eating_out', 'transport') (optional)
        is_load: Whether this is a top-up transaction
        settled: Settlement timestamp when transaction completed (optional)
        merchant: Merchant ID or expanded merchant object (optional)
        metadata: Custom key-value metadata
        notes: User-added notes for the transaction (optional)
        decline_reason: Reason for transaction decline (optional, declined only)
        model_config: Pydantic model configuration
    """

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
            "Transaction category (e.g., 'eating_out', 'transport', 'groceries', "
            "'income', 'savings', 'transfers')"
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
            "CARD_CLOSED",
            "CARD_EXPIRED",
            "INVALID_EXPIRY_DATE",
            "INVALID_PIN",
            "SCA_NOT_AUTHENTICATED_CARD_NOT_PRESENT",
            "AUTHENTICATION_REJECTED_BY_CARDHOLDER",
        ]
        | None
    ) = Field(
        None,
        description=(
            "Reason for transaction decline (only present on declined transactions)"
        ),
    )
    counterparty: Counterparty | None = Field(
        None, description="Transaction counterparty"
    )

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._client: BaseSyncClient | BaseAsyncClient | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to set up client if available.

        Args:
            __context: Pydantic context
        """
        super().model_post_init(__context)

    def _ensure_client(self) -> BaseSyncClient | BaseAsyncClient:
        """Ensure client is available for API calls.

        Returns:
            The client instance

        Raises:
            RuntimeError: If no client is available
        """
        if self._client is None:
            raise RuntimeError(
                "No client available. Transaction must be retrieved from MonzoClient "
                "to use methods."
            )
        return self._client

    def _set_client(self, client: BaseSyncClient | BaseAsyncClient) -> Transaction:
        """Set the client for this transaction instance.

        Args:
            client: The client instance to set

        Returns:
            The transaction instance with client set
        """
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
            RuntimeError: If no client is available or if using async client
        """
        from ..api.attachments import AttachmentsAPI
        from ..core import BaseSyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseSyncClient):
            raise RuntimeError(
                "Sync method called on transaction with async client. "
                "Use aupload_attachment() instead or retrieve transaction "
                "from MonzoClient."
            )

        attachments_api = AttachmentsAPI(client)
        return attachments_api.upload(
            transaction_id=self.id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
        )

    def annotate(self, metadata: dict[str, Any]) -> Transaction:
        """Add annotations to this transaction.

        Args:
            metadata: Key-value metadata to store

        Returns:
            Updated transaction
        """
        client = cast("BaseSyncClient", self._ensure_client())

        data = {}
        for key, value in metadata.items():
            if value == "":
                data[f"metadata[{key}]"] = ""
            else:
                data[f"metadata[{key}]"] = str(value)

        response = client._patch(f"/transactions/{self.id}", data=data)
        transaction_response = TransactionResponse(**response.json())
        updated_transaction = transaction_response.transaction
        updated_transaction._set_client(client)
        return updated_transaction

    def refresh(self, expand: list[str] | None = None) -> Transaction:
        """Refresh this transaction with latest data from the API.

        Args:
            expand: Fields to expand (e.g., ['merchant'])

        Returns:
            Refreshed transaction
        """
        client = cast("BaseSyncClient", self._ensure_client())
        expand_params = client._prepare_expand_params(expand)

        response = client._get(f"/transactions/{self.id}", params=expand_params)
        transaction_response = TransactionResponse(**response.json())
        updated_transaction = transaction_response.transaction
        updated_transaction._set_client(client)
        return updated_transaction

    async def aupload_attachment(
        self,
        file_path: str | Path,
        file_name: str | None = None,
        file_type: str | None = None,
    ) -> Attachment:
        """Upload and attach a file to this transaction (async version).

        Args:
            file_path: Path to the file to upload
            file_name: Custom name for the file (defaults to filename from path)
            file_type: MIME type (inferred from file extension if not provided)

        Returns:
            The uploaded attachment

        Raises:
            RuntimeError: If no client is available or if using sync client
        """
        from ..api.async_attachments import AsyncAttachmentsAPI
        from ..core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on transaction with sync client. "
                "Use upload_attachment() instead or retrieve transaction "
                "from AsyncMonzoClient."
            )

        attachments_api = AsyncAttachmentsAPI(client)
        return await attachments_api.upload(
            transaction_id=self.id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
        )

    async def aannotate(self, metadata: dict[str, Any]) -> Transaction:
        """Add annotations to this transaction (async version).

        Args:
            metadata: Key-value metadata to store

        Returns:
            Updated transaction

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from ..core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on transaction with sync client. "
                "Use annotate() instead or retrieve transaction from AsyncMonzoClient."
            )

        data = {}
        for key, value in metadata.items():
            if value == "":
                data[f"metadata[{key}]"] = ""
            else:
                data[f"metadata[{key}]"] = str(value)

        response = await client._patch(f"/transactions/{self.id}", data=data)
        transaction_response = TransactionResponse(**response.json())
        updated_transaction = transaction_response.transaction
        updated_transaction._set_client(client)
        return updated_transaction

    async def arefresh(self, expand: list[str] | None = None) -> Transaction:
        """Refresh this transaction with latest data from the API (async version).

        Args:
            expand: Fields to expand (e.g., ['merchant'])

        Returns:
            Refreshed transaction

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from ..core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on transaction with sync client. "
                "Use refresh() instead or retrieve transaction from AsyncMonzoClient."
            )
        expand_params = client._prepare_expand_params(expand)

        response = await client._get(f"/transactions/{self.id}", params=expand_params)
        transaction_response = TransactionResponse(**response.json())
        updated_transaction = transaction_response.transaction
        updated_transaction._set_client(client)
        return updated_transaction

    @field_validator("settled", mode="before")
    @classmethod
    def validate_settled(cls, v: str | None) -> str | None:
        """Convert empty strings to None for settled field.

        Args:
            v: The settled field value

        Returns:
            None if empty string, otherwise returns input unchanged
        """
        if v == "":
            return None
        return v


class TransactionsResponse(BaseModel):
    """Transactions list response."""

    transactions: list[Transaction] = Field(..., description="List of transactions")


class TransactionResponse(BaseModel):
    """Single transaction response."""

    transaction: Transaction = Field(..., description="Single transaction object")
