"""Pot-related models."""

from datetime import datetime

from pydantic import BaseModel, Field


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


# Response containers
class PotsResponse(BaseModel):
    """Pots list response."""

    pots: list[Pot] = Field(..., description="List of user pots")
