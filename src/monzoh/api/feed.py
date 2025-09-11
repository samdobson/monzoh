"""Feed Items API endpoints."""

from ..core import BaseSyncClient
from ..models.feed import FeedItemParams


class FeedAPI:
    """Feed Items API client."""

    def __init__(self, client: BaseSyncClient) -> None:
        """Initialize feed API.

        Args:
            client: Base API client
        """
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

        # Extract url as top-level field
        if "url" in params_dict:
            data["url"] = params_dict.pop("url")

        # Add remaining params with params[] prefix
        for key, value in params_dict.items():
            data[f"params[{key}]"] = value

        self.client._post("/feed", data=data)
