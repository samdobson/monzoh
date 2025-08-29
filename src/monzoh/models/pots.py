"""Pot-related models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..core import BaseSyncClient


class Pot(BaseModel):
    """Represents a pot."""

    id: str = Field(..., description="Unique pot identifier")
    name: str = Field(..., description="User-defined pot name")
    style: str = Field(
        ..., description="Pot visual style/theme (e.g., 'beach_ball', 'blue')"
    )
    balance: int = Field(
        ...,
        description=(
            "Pot balance in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    created: datetime = Field(..., description="Pot creation timestamp")
    updated: datetime = Field(..., description="Last pot update timestamp")
    deleted: bool = Field(False, description="Whether the pot is deleted")
    account_id: str | None = Field(None, description="Associated account identifier")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._client: BaseSyncClient | None = None
        self._source_account_id: str | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to set up client if available."""
        super().model_post_init(__context)

    def _ensure_client(self) -> BaseSyncClient:
        """Ensure client is available for API calls."""
        if self._client is None:
            raise RuntimeError(
                "No client available. Pot must be retrieved from MonzoClient "
                "to use methods."
            )
        return self._client

    def _set_client(self, client: BaseSyncClient) -> Pot:
        """Set the client for this pot instance."""
        self._client = client
        return self

    def _get_source_account_id(self) -> str:
        """Get the source account ID for this pot."""
        if self._source_account_id:
            return self._source_account_id
        if self.account_id:
            return self.account_id
        raise RuntimeError(
            "No source account ID available. Cannot perform pot operations."
        )

    def deposit(self, amount: int, dedupe_id: str | None = None) -> Pot:
        """Deposit money into this pot.

        Args:
            amount: Amount in minor units (e.g., pennies)
            dedupe_id: Unique ID to prevent duplicate deposits
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        client = self._ensure_client()
        source_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        data = {
            "source_account_id": source_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = client._put(f"/pots/{self.id}/deposit", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot

    def withdraw(
        self,
        amount: int,
        destination_account_id: str | None = None,
        dedupe_id: str | None = None,
    ) -> Pot:
        """Withdraw money from this pot.

        Args:
            amount: Amount in minor units (e.g., pennies)
            destination_account_id: Destination account ID
                (uses source account if not provided)
            dedupe_id: Unique ID to prevent duplicate withdrawals
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        client = self._ensure_client()

        if destination_account_id is None:
            destination_account_id = self._get_source_account_id()

        if dedupe_id is None:
            dedupe_id = str(uuid4())

        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = client._put(f"/pots/{self.id}/withdraw", data=data)
        updated_pot = Pot(**response.json())
        updated_pot._set_client(client)
        updated_pot._source_account_id = self._source_account_id
        return updated_pot


# Response containers
class PotsResponse(BaseModel):
    """Pots list response."""

    pots: list[Pot] = Field(..., description="List of user pots")
