"""Base models and common types."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OAuthToken(BaseModel):
    """OAuth token response."""

    access_token: str = Field(..., description="Access token for API authentication")
    client_id: str = Field(..., description="Client identifier")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    refresh_token: str | None = Field(
        None, description="Refresh token (only for confidential clients)"
    )
    token_type: str = Field("Bearer", description="Token type (always 'Bearer')")
    user_id: str = Field(..., description="User identifier")


class WhoAmI(BaseModel):
    """Who am I response."""

    authenticated: bool = Field(..., description="Whether the request is authenticated")
    client_id: str = Field(..., description="Client identifier")
    user_id: str = Field(..., description="User identifier")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: int | None = Field(
        None, ge=1, le=100, description="Number of results per page (1-100, default 30)"
    )
    since: datetime | str | None = Field(
        None, description="Start time (RFC3339 timestamp) or object ID"
    )
    before: datetime | None = Field(None, description="End time (RFC3339 timestamp)")


class ExpandParams(BaseModel):
    """Expand parameters."""

    expand: list[str] | None = Field(
        None, description="List of related objects to expand inline"
    )


def convert_amount_to_minor_units(amount: float | Decimal | str) -> int:
    """Convert amount from major units to minor units.

    Args:
        amount: Amount in major units (e.g., pounds, euros, dollars)

    Returns:
        Amount in minor units (e.g., pennies, cents)

    Raises:
        ValueError: If amount is negative or invalid

    Examples:
        >>> convert_amount_to_minor_units(1.50)
        150
        >>> convert_amount_to_minor_units("10.99")
        1099
        >>> convert_amount_to_minor_units(5)
        500
    """
    try:
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, int | float):
            amount = Decimal(str(amount))
    except (ValueError, TypeError, ArithmeticError) as e:
        msg = f"Invalid amount '{amount}': {e}"
        raise ValueError(msg) from e

    if amount < 0:
        msg = "Amount cannot be negative"
        raise ValueError(msg)

    return int(amount * 100)


def convert_amount_from_minor_units(amount: int) -> Decimal:
    """Convert amount from minor units to major units.

    Args:
        amount: Amount in minor units (e.g., pennies, cents)

    Returns:
        Amount in major units as Decimal

    Examples:
        >>> convert_amount_from_minor_units(150)
        Decimal('1.50')
        >>> convert_amount_from_minor_units(1099)
        Decimal('10.99')
    """
    return Decimal(amount) / 100
