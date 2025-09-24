"""Async webhooks API endpoints."""

from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Webhook, WebhookResponse, WebhooksResponse


class AsyncWebhooksAPI:
    """Async webhooks API client.

    Args:
        client: Base async API client
    """

    def __init__(self, client: BaseAsyncClient) -> None:
        self.client = client

    async def register(self, account_id: str, url: str) -> Webhook:
        """Register a webhook for an account.

        Args:
            account_id: Account ID
            url: Webhook URL

        Returns:
            Registered webhook
        """
        data = {
            "account_id": account_id,
            "url": url,
        }

        response = await self.client._post("/webhooks", data=data)
        webhook_response = WebhookResponse(**response.json())
        return webhook_response.webhook

    async def list(self, account_id: str) -> list[Webhook]:
        """List webhooks for an account.

        Args:
            account_id: Account ID

        Returns:
            List of registered webhooks
        """
        params = {"account_id": account_id}

        response = await self.client._get("/webhooks", params=params)
        webhooks_response = WebhooksResponse(**response.json())
        return webhooks_response.webhooks

    async def delete(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            None
        """
        await self.client._delete(f"/webhooks/{webhook_id}")
