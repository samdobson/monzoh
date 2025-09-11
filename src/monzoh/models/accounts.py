"""Account-related models."""

from __future__ import annotations

import builtins
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, cast

from pydantic import BaseModel, Field, field_validator

from .base import convert_amount_from_minor_units

if TYPE_CHECKING:
    from ..core import BaseSyncClient
    from ..core.async_base import BaseAsyncClient
    from .feed import FeedItemParams
    from .pots import Pot
    from .transactions import Transaction


class Account(BaseModel):
    """Represents a Monzo account."""

    id: str = Field(..., description="Unique account identifier")
    description: str = Field(..., description="Human-readable account description")
    created: datetime = Field(..., description="Account creation timestamp")
    closed: bool = Field(False, description="Whether the account is closed")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: Any) -> None:
        """Initialize Account model.

        Args:
            **data: Account data fields
        """
        super().__init__(**data)
        self._client: BaseSyncClient | BaseAsyncClient | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to set up client if available."""
        super().model_post_init(__context)

    def _ensure_client(self) -> BaseSyncClient | BaseAsyncClient:
        """Ensure client is available for API calls."""
        if self._client is None:
            raise RuntimeError(
                "No client available. Account must be retrieved from MonzoClient "
                "to use methods."
            )
        return self._client

    def _set_client(self, client: BaseSyncClient | BaseAsyncClient) -> Account:
        """Set the client for this account instance."""
        self._client = client
        return self

    def get_balance(self) -> Balance:
        """Get balance information for this account.

        Returns:
            Account balance information
        """
        client = cast("BaseSyncClient", self._ensure_client())
        params = {"account_id": self.id}
        response = client._get("/balance", params=params)
        return Balance(**response.json())

    def list_transactions(
        self,
        expand: builtins.list[str] | None = None,
        limit: int | None = None,
        since: datetime | str | None = None,
        before: datetime | None = None,
    ) -> builtins.list[Transaction]:
        """List transactions for this account.

        Args:
            expand: Fields to expand (e.g., ['merchant'])
            limit: Maximum number of results (1-100)
            since: Start time as RFC3339 timestamp or transaction ID
            before: End time as RFC3339 timestamp

        Returns:
            List of transactions
        """
        from .transactions import TransactionsResponse

        client = cast("BaseSyncClient", self._ensure_client())
        params = {"account_id": self.id}

        # Add pagination parameters
        pagination_params = client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        # Add expand parameters
        expand_params = client._prepare_expand_params(expand)
        if expand_params:
            params_list = list(params.items()) + expand_params
            response = client._get("/transactions", params=params_list)
        else:
            response = client._get("/transactions", params=params)

        transactions_response = TransactionsResponse(**response.json())

        # Set client on all transaction objects
        for transaction in transactions_response.transactions:
            transaction._set_client(client)

        return transactions_response.transactions

    def list_pots(self) -> builtins.list[Pot]:
        """List pots for this account.

        Returns:
            List of pots
        """
        from .pots import PotsResponse

        client = cast("BaseSyncClient", self._ensure_client())
        params = {"current_account_id": self.id}

        response = client._get("/pots", params=params)
        pots_response = PotsResponse(**response.json())

        # Set client and source account on all pot objects
        for pot in pots_response.pots:
            pot._set_client(client)
            pot._source_account_id = self.id

        return pots_response.pots

    def create_feed_item(
        self,
        params: FeedItemParams,
    ) -> None:
        """Create a feed item for this account.

        Args:
            params: Feed item parameters

        Returns:
            None
        """
        client = cast("BaseSyncClient", self._ensure_client())
        data = {
            "account_id": self.id,
            "type": "basic",
        }

        params_dict = params.model_dump(exclude_none=True)

        # Extract url as top-level field
        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

        # Add remaining params with params[] prefix
        for key, value in params_dict.items():
            data[f"params[{key}]"] = value

        client._post("/feed", data=data)

    # Async methods
    async def aget_balance(self) -> Balance:
        """Get balance information for this account (async version).

        Returns:
            Account balance information
        """
        from ..core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on account with sync client. "
                "Use get_balance() instead or retrieve account from AsyncMonzoClient."
            )
        params = {"account_id": self.id}
        response = await client._get("/balance", params=params)
        return Balance(**response.json())

    async def alist_transactions(
        self,
        expand: builtins.list[str] | None = None,
        limit: int | None = None,
        since: datetime | str | None = None,
        before: datetime | None = None,
    ) -> builtins.list[Transaction]:
        """List transactions for this account (async version).

        Args:
            expand: Fields to expand (e.g., ['merchant'])
            limit: Maximum number of results (1-100)
            since: Start time as RFC3339 timestamp or transaction ID
            before: End time as RFC3339 timestamp

        Returns:
            List of transactions
        """
        from ..core.async_base import BaseAsyncClient
        from .transactions import TransactionsResponse

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on account with sync client. "
                "Use list_transactions() instead or retrieve account from "
                "AsyncMonzoClient."
            )
        params = {"account_id": self.id}

        # Add pagination parameters
        pagination_params = client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        # Add expand parameters
        expand_params = client._prepare_expand_params(expand)
        if expand_params:
            params_list = list(params.items()) + expand_params
            response = await client._get("/transactions", params=params_list)
        else:
            response = await client._get("/transactions", params=params)

        transactions_response = TransactionsResponse(**response.json())

        # Set client on all transaction objects
        for transaction in transactions_response.transactions:
            transaction._set_client(client)

        return transactions_response.transactions

    async def alist_pots(self) -> builtins.list[Pot]:
        """List pots for this account (async version).

        Returns:
            List of pots
        """
        from ..core.async_base import BaseAsyncClient
        from .pots import PotsResponse

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on account with sync client. "
                "Use list_pots() instead or retrieve account from AsyncMonzoClient."
            )
        params = {"current_account_id": self.id}

        response = await client._get("/pots", params=params)
        pots_response = PotsResponse(**response.json())

        # Set client and source account on all pot objects
        for pot in pots_response.pots:
            pot._set_client(client)
            pot._source_account_id = self.id

        return pots_response.pots

    async def acreate_feed_item(
        self,
        params: FeedItemParams,
    ) -> None:
        """Create a feed item for this account (async version).

        Args:
            params: Feed item parameters

        Returns:
            None
        """
        from ..core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            raise RuntimeError(
                "Async method called on account with sync client. "
                "Use create_feed_item() instead or retrieve account from "
                "AsyncMonzoClient."
            )
        data = {
            "account_id": self.id,
            "type": "basic",
        }

        params_dict = params.model_dump(exclude_none=True)

        # Extract url as top-level field
        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

        # Add remaining params with params[] prefix
        for key, value in params_dict.items():
            data[f"params[{key}]"] = value

        await client._post("/feed", data=data)


class AccountType(BaseModel):
    """Account type filter."""

    account_type: Literal["uk_retail", "uk_retail_joint"] = Field(
        ..., description="Type of account"
    )


class Balance(BaseModel):
    """Account balance information."""

    balance: Decimal = Field(
        ...,
        description=(
            "Available balance in major units of the currency, "
            "eg. pounds for GBP, or euros/dollars for EUR and USD"
        ),
    )
    total_balance: Decimal = Field(
        ...,
        description=(
            "Total balance including pots in major units of the currency, "
            "eg. pounds for GBP, or euros/dollars for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    spend_today: Decimal = Field(
        ...,
        description=(
            "Amount spent today in major units of the currency, "
            "eg. pounds for GBP, or euros/dollars for EUR and USD"
        ),
    )

    @field_validator("balance", "total_balance", "spend_today", mode="before")
    @classmethod
    def convert_minor_to_major_units(cls, v: int) -> Decimal:
        """Convert balance from minor units (API response) to major units."""
        return convert_amount_from_minor_units(v)


# Response containers
class AccountsResponse(BaseModel):
    """Accounts list response."""

    accounts: list[Account] = Field(..., description="List of user accounts")
