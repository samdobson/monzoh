"""Base models and common types."""

from datetime import datetime

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
