"""Async feed Items API endpoints."""

from monzoh.core.async_base import BaseAsyncClient
from monzoh.models.feed import FeedItemParams


class AsyncFeedAPI:
    """Async feed Items API client.

    Args:
        client: Base async API client
    """

    def __init__(self, client: BaseAsyncClient) -> None:
        self.client = client

    async def create_item(
        self,
        account_id: str,
        params: FeedItemParams,
    ) -> None:
        """Create a feed item.

        Args:
            account_id: Account ID
            params: Feed item parameters

        Returns:
            None
        """
        data = {
            "account_id": account_id,
            "type": "basic",
        }

        params_dict = params.model_dump(exclude_none=True)

        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

        for key, value in params_dict.items():
            data[f"params[{key}]"] = value

        await self.client._post("/feed", data=data)
