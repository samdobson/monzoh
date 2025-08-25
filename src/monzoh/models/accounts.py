"""Account-related models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Account(BaseModel):
    """Represents a Monzo account."""

    id: str = Field(..., description="Unique account identifier")
    description: str = Field(..., description="Human-readable account description")
    created: datetime = Field(..., description="Account creation timestamp")
    closed: bool = Field(False, description="Whether the account is closed")


class AccountType(BaseModel):
    """Account type filter."""

    account_type: Literal["uk_retail", "uk_retail_joint"] = Field(
        ..., description="Type of account"
    )


class Balance(BaseModel):
    """Account balance information."""

    balance: int = Field(
        ...,
        description=(
            "Available balance in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    total_balance: int = Field(
        ...,
        description=(
            "Total balance including pots in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    spend_today: int = Field(
        ...,
        description=(
            "Amount spent today in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )


# Response containers
class AccountsResponse(BaseModel):
    """Accounts list response."""

    accounts: list[Account] = Field(..., description="List of user accounts")
