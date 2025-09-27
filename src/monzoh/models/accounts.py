"""Account-related models."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003
from typing import TYPE_CHECKING, Literal, cast

from pydantic import BaseModel, Field, field_validator

from .base import convert_amount_from_minor_units

if TYPE_CHECKING:
    import builtins

    from monzoh.core import BaseSyncClient
    from monzoh.core.async_base import BaseAsyncClient

    from .feed import FeedItemParams
    from .pots import Pot
    from .transactions import Transaction


class AccountOwner(BaseModel):
    """Represents an account owner.

    Attributes:
        user_id: User identifier
        preferred_name: Preferred display name
        preferred_first_name: Preferred first name
    """

    user_id: str | None = Field(None, description="User identifier")
    preferred_name: str | None = Field(None, description="Preferred display name")
    preferred_first_name: str | None = Field(None, description="Preferred first name")


class Account(BaseModel):
    """Represents a Monzo account.

    Args:
        **data: Account data fields

    Attributes:
        id: Unique account identifier
        description: Human-readable account description
        created: Account creation timestamp
        closed: Whether the account is closed
        model_config: Pydantic model configuration
    """

    id: str = Field(..., description="Unique account identifier")
    description: str = Field(..., description="Human-readable account description")
    created: datetime = Field(..., description="Account creation timestamp")
    closed: bool = Field(default=False, description="Whether the account is closed")
    type: str | None = Field(None, description="Account type")
    currency: str | None = Field(None, description="Account currency")
    country_code: str | None = Field(None, description="Country code")
    owners: list[AccountOwner] | None = Field(None, description="Account owners")

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        self._client: BaseSyncClient | BaseAsyncClient | None = None

    def model_post_init(self, __context: object, /) -> None:
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
            msg = (
                "No client available. Account must be retrieved from MonzoClient "
                "to use methods."
            )
            raise RuntimeError(msg)
        return self._client

    def _set_client(self, client: BaseSyncClient | BaseAsyncClient) -> Account:
        """Set the client for this account instance.

        Args:
            client: The client instance to set

        Returns:
            The account instance with client set
        """
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

        pagination_params = client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        expand_params = client._prepare_expand_params(expand)
        if expand_params:
            params_list = list(params.items()) + expand_params
            response = client._get("/transactions", params=params_list)
        else:
            response = client._get("/transactions", params=params)

        transactions_response = TransactionsResponse(**response.json())

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
        """
        client = cast("BaseSyncClient", self._ensure_client())
        data = {
            "account_id": self.id,
            "type": "basic",
        }

        params_dict = params.model_dump(exclude_none=True)

        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

        for key, value in params_dict.items():
            data[f"params[{key}]"] = value

        client._post("/feed", data=data)

    async def aget_balance(self) -> Balance:
        """Get balance information for this account (async version).

        Returns:
            Account balance information

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on account with sync client. "
                "Use get_balance() instead or retrieve account from AsyncMonzoClient."
            )
            raise TypeError(msg)
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

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        from .transactions import TransactionsResponse

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on account with sync client. "
                "Use list_transactions() instead or retrieve account from "
                "AsyncMonzoClient."
            )
            raise TypeError(msg)
        params = {"account_id": self.id}

        pagination_params = client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        expand_params = client._prepare_expand_params(expand)
        if expand_params:
            params_list = list(params.items()) + expand_params
            response = await client._get("/transactions", params=params_list)
        else:
            response = await client._get("/transactions", params=params)

        transactions_response = TransactionsResponse(**response.json())

        for transaction in transactions_response.transactions:
            transaction._set_client(client)

        return transactions_response.transactions

    async def alist_pots(self) -> builtins.list[Pot]:
        """List pots for this account (async version).

        Returns:
            List of pots

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        from .pots import PotsResponse

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on account with sync client. "
                "Use list_pots() instead or retrieve account from AsyncMonzoClient."
            )
            raise TypeError(msg)
        params = {"current_account_id": self.id}

        response = await client._get("/pots", params=params)
        pots_response = PotsResponse(**response.json())

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

        Raises:
            RuntimeError: If no client is available or wrong client type
        """
        from monzoh.core.async_base import BaseAsyncClient

        client = self._ensure_client()
        if not isinstance(client, BaseAsyncClient):
            msg = (
                "Async method called on account with sync client. "
                "Use create_feed_item() instead or retrieve account from "
                "AsyncMonzoClient."
            )
            raise TypeError(msg)
        data = {
            "account_id": self.id,
            "type": "basic",
        }

        params_dict = params.model_dump(exclude_none=True)

        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

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
    balance_including_flexible_savings: bool = Field(
        ..., description="Whether balance includes flexible savings pots"
    )
    local_currency: str = Field(..., description="Local currency")
    local_exchange_rate: Decimal = Field(..., description="Local exchange rate")
    local_spend: Decimal = Field(
        ...,
        description=("Local spend in major units of the local currency"),
    )

    @field_validator(
        "balance", "total_balance", "spend_today", "local_spend", mode="before"
    )
    @classmethod
    def convert_minor_to_major_units(cls, v: int) -> Decimal:
        """Convert balance from minor units (API response) to major units.

        Args:
            v: Amount in minor units

        Returns:
            Amount in major units as Decimal
        """
        return convert_amount_from_minor_units(v)


class AccountsResponse(BaseModel):
    """Accounts list response."""

    accounts: list[Account] = Field(..., description="List of user accounts")


# Rebuild models to resolve forward references
Account.model_rebuild()
Balance.model_rebuild()
AccountsResponse.model_rebuild()
