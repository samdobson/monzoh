"""Feed-related models."""

from pydantic import BaseModel, Field


class FeedItemParams(BaseModel):
    """Feed item parameters."""

    title: str = Field(..., description="Title text to display in the feed item")
    image_url: str = Field(
        ..., description="URL of image to display (supports animated GIFs)"
    )
    body: str | None = Field(None, description="Optional body text for the feed item")
    background_color: str | None = Field(
        None, description="Hex color for background (#RRGGBB format)"
    )
    title_color: str | None = Field(
        None, description="Hex color for title text (#RRGGBB format)"
    )
    body_color: str | None = Field(
        None, description="Hex color for body text (#RRGGBB format)"
    )
