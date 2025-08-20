"""Webhook-related models."""

from typing import Any

from pydantic import BaseModel, Field


class Webhook(BaseModel):
    """Represents a webhook."""

    id: str = Field(..., description="Unique webhook identifier")
    account_id: str = Field(..., description="Account to receive notifications for")
    url: str = Field(..., description="URL to send webhook notifications to")


class WebhookEvent(BaseModel):
    """Webhook event."""

    type: str = Field(..., description="Event type (e.g., 'transaction.created')")
    data: dict[str, Any] = Field(..., description="Event data payload")


# Response containers
class WebhooksResponse(BaseModel):
    """Webhooks list response."""

    webhooks: list[Webhook] = Field(..., description="List of registered webhooks")


class WebhookResponse(BaseModel):
    """Single webhook response."""

    webhook: Webhook = Field(..., description="Single webhook object")
