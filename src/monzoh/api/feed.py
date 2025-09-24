"""Feed Items API endpoints."""

from monzoh.core import BaseSyncClient
from monzoh.models.feed import FeedItemParams


class FeedAPI:
    """Feed Items API client.

    Args:
        client: Base API client
    """

    def __init__(self, client: BaseSyncClient) -> None:
        self.client = client

    def create_item(
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

        self.client._post("/feed", data=data)
