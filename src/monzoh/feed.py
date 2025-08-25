"""Feed Items API endpoints."""


from .client import BaseSyncClient


class FeedAPI:
    """Feed Items API client."""

    def __init__(self, client: BaseSyncClient) -> None:
        """Initialize feed API.

        Args:
            client: Base API client
        """
        self.client = client

    def create_basic_item(
        self,
        account_id: str,
        title: str,
        image_url: str,
        body: str | None = None,
        url: str | None = None,
        background_color: str | None = None,
        title_color: str | None = None,
        body_color: str | None = None,
    ) -> None:
        """Create a basic feed item.

        Args:
            account_id: Account ID
            title: Feed item title
            image_url: Image URL
            body: Optional body text
            url: Optional URL to open when tapped
            background_color: Background color in hex (#RRGGBB)
            title_color: Title text color in hex (#RRGGBB)
            body_color: Body text color in hex (#RRGGBB)

        Returns:
            None
        """
        data = {
            "account_id": account_id,
            "type": "basic",
            "params[title]": title,
            "params[image_url]": image_url,
        }

        if body:
            data["params[body]"] = body
        if url:
            data["url"] = url
        if background_color:
            data["params[background_color]"] = background_color
        if title_color:
            data["params[title_color]"] = title_color
        if body_color:
            data["params[body_color]"] = body_color

        self.client._post("/feed", data=data)
