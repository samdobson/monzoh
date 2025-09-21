"""Pot-related models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from .base import convert_amount_from_minor_units, convert_amount_to_minor_units

if TYPE_CHECKING:
    from monzoh.core import BaseSyncClient
    from monzoh.core.async_base import BaseAsyncClient


class Pot(BaseModel):
    """Represents a pot.

    Args:
        **data: Pot data fields

    Attributes:
        id: Unique pot identifier
        name: User-defined pot name
        style: Pot visual style/theme (e.g., 'beach_ball', 'blue')
        balance: Pot balance in major units of the currency
        currency: ISO 4217 currency code
        created: Pot creation timestamp
        updated: Last pot update timestamp
        deleted: Whether the pot is deleted
        account_id: Associated account identifier (optional)
        goal_amount: Pot goal amount in major units (optional)
        type: Pot type (optional)
        product_id: Product ID (optional)
        current_account_id: Current account ID (optional)
        cover_image_url: Cover image URL (optional)
        isa_wrapper: ISA wrapper (optional)
        round_up: Whether to use transfer money from rounding up transactions (optional)
        round_up_multiplier: Rounding up multiplier (optional)
        is_tax_pot: Whether the pot is taxed (optional)
        locked: Whether the pot is locked (optional)
        available_for_bills: Whether the pot is available for bills (optional)
        has_virtual_cards: Whether the pot has linked virtual cards (optional)
        model_config: Pydantic model configuration
    """

    id: str = Field(..., description="Unique pot identifier")
    name: str = Field(..., description="User-defined pot name")
    style: str = Field(
        ..., description="Pot visual style/theme (e.g., 'beach_ball', 'blue')"
    )
    balance: Decimal = Field(
        ...,
        description=(
            "Pot balance in major units of the currency, "
            "eg. pounds for GBP, or euros/dollars for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    created: datetime = Field(..., description="Pot creation timestamp")
    updated: datetime = Field(..., description="Last pot update timestamp")
    deleted: bool = Field(False, description="Whether the pot is deleted")
    account_id: str | None = Field(None, description="Associated account identifier")
    goal_amount: Decimal | None = Field(
        None,
        description=(
            "Pot goal amount in major units of the currency, "
            "eg. pounds for GBP, or euros/dollars for EUR and USD"
        ),
    )
    type: str | None = Field(None, description="Pot type")
    product_id: str | None = Field(None, description="Product ID")
    current_account_id: str | None = Field(None, description="Current account ID")
    cover_image_url: str | None = Field(None, description="Cover image URL")
    isa_wrapper: str | None = Field(None, description="ISA wrapper")
    round_up: bool | None = Field(
        None,
        description=(
            "Whether to use transfer money from rounding up transactions to the pot. "
            "You can only switch on round ups for one pot at a time"
        ),
    )
    round_up_multiplier: int | None = Field(None, description="Rounding up multiplier")
    is_tax_pot: bool | None = Field(None, description="Whether the pot is taxed")
    locked: bool | None = Field(None, description="Whether the pot is locked")
    available_for_bills: bool | None = Field(
        None, description="Whether the pot is available for bills"
    )
    has_virtual_cards: bool | None = Field(
        None, description="Whether the pot has linked virtual cards"
    )

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._client: BaseSyncClient | BaseAsyncClient | None = None
        self._source_account_id: str | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to set up client if available."""
        super().model_post_init(__context)

    @field_validator("balance", mode="before")
    @classmethod
    def convert_balance_minor_to_major_units(cls, v: int) -> Decimal:
        """Convert balance from minor units (API response) to major units."""
        return convert_amount_from_minor_units(v)

    @field_validator("goal_amount", mode="before")
    @classmethod
    def convert_goal_amount_minor_to_major_units(cls, v: int | None) -> Decimal | None:
        """Convert goal_amount from minor units (API response) to major units."""
        if v is None:
            return None
        return convert_amount_from_minor_units(v)

    def _ensure_client(self) -> BaseSyncClient | BaseAsyncClient:
        """Ensure client is available for API calls."""
        if self._client is None:
            msg = (
                "No client available. Pot must be retrieved from MonzoClient "
                "to use methods."
            )
            raise RuntimeError(msg)
        return self._client

    def _set_client(self, client: BaseSyncClient | BaseAsyncClient) -> Pot:
        """Set the client for this pot instance."""
        self._client = client
        return self

    def _get_source_account_id(self) -> str:
        """Get the source account ID for this pot."""
        if self._source_account_id:
            return self._source_account_id
        if self.account_id:
            return self.account_id
        msg = "No source account ID available. Cannot perform pot operations."
        raise RuntimeError(msg)

    def deposit(
        self, amount: float | Decimal | str, dedupe_id: str | None = None
    ) -> Pot:
        """Deposit money into this pot.

        Args:
            amount: Amount in major units (e.g., 1.50 for £1.50)
            dedupe_id: Unique ID to prevent duplicate deposits
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        client = cast("BaseSyncClient", self._ensure_client())
        source_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "source_account_id": source_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = client._put(f"/pots/{self.id}/deposit", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot

    def withdraw(
        self,
        amount: float | Decimal | str,
        destination_account_id: str | None = None,
        dedupe_id: str | None = None,
    ) -> Pot:
        """Withdraw money from this pot.

        Args:
            amount: Amount in major units (e.g., 1.50 for £1.50)
            destination_account_id: Destination account ID
                (uses source account if not provided)
            dedupe_id: Unique ID to prevent duplicate withdrawals
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        client = cast("BaseSyncClient", self._ensure_client())

        if destination_account_id is None:
            destination_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = client._put(f"/pots/{self.id}/withdraw", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot

    async def adeposit(
        self, amount: float | Decimal | str, dedupe_id: str | None = None
    ) -> Pot:
        """Deposit money into this pot (async version).

        Args:
            amount: Amount in major units (e.g., 1.50 for £1.50)
            dedupe_id: Unique ID to prevent duplicate deposits
                (auto-generated if not provided)

        Returns:
            Updated pot

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on pot with sync client. "
                "Use deposit() instead or retrieve pot from AsyncMonzoClient."
            )
            raise RuntimeError(msg)
        source_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "source_account_id": source_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = await client._put(f"/pots/{self.id}/deposit", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot

    async def awithdraw(
        self,
        amount: float | Decimal | str,
        destination_account_id: str | None = None,
        dedupe_id: str | None = None,
    ) -> Pot:
        """Withdraw money from this pot (async version).

        Args:
            amount: Amount in major units (e.g., 1.50 for £1.50)
            destination_account_id: Destination account ID
                (uses source account if not provided)
            dedupe_id: Unique ID to prevent duplicate withdrawals
                (auto-generated if not provided)

        Returns:
            Updated pot

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on pot with sync client. "
                "Use withdraw() instead or retrieve pot from AsyncMonzoClient."
            )
            raise RuntimeError(msg)

        if destination_account_id is None:
            destination_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = await client._put(f"/pots/{self.id}/withdraw", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot


class PotsResponse(BaseModel):
    """Pots list response."""

    pots: list[Pot] = Field(..., description="List of user pots")
