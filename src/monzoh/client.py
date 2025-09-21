"""Main Monzo API client."""

from typing import Any

import httpx
from rich.console import Console

from .api import (
    AccountsAPI,
    AttachmentsAPI,
    FeedAPI,
    PotsAPI,
    ReceiptsAPI,
    TransactionsAPI,
    WebhooksAPI,
)
from .auth import MonzoOAuth
from .cli import load_env_credentials, load_token_from_cache, try_refresh_token
from .core import BaseSyncClient
from .models import WhoAmI


def _load_cached_token() -> str | None:
    """Load access token from cache, refreshing if expired.

    Returns:
        Access token if available, None otherwise
    """
    try:
        cached_token = load_token_from_cache()
        if cached_token and isinstance(cached_token, dict):
            access_token = cached_token.get("access_token")
            if isinstance(access_token, str):
                return access_token

        expired_token = load_token_from_cache(include_expired=True)
        if expired_token and isinstance(expired_token, dict):
            credentials = load_env_credentials()
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            redirect_uri = credentials.get("redirect_uri")

            if client_id and client_secret and redirect_uri:
                oauth = MonzoOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                )

                console = Console(file=None, quiet=True)

                refreshed_token = try_refresh_token(expired_token, oauth, console)
                if refreshed_token:
                    return refreshed_token

        return None
    except (AttributeError, TypeError, ValueError, KeyError):
        return None


class MonzoClient:
    """Main Monzo API client.

    Args:
        access_token: OAuth access token. If not provided, will attempt to
            load from cache.
        http_client: Optional httpx client to use
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        access_token: str | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        effective_token = access_token or _load_cached_token()

        self._base_client = BaseSyncClient(
            access_token=effective_token, http_client=http_client, timeout=timeout
        )

        self.accounts = AccountsAPI(self._base_client)
        self.transactions = TransactionsAPI(self._base_client)
        self.pots = PotsAPI(self._base_client)
        self.attachments = AttachmentsAPI(self._base_client)
        self.feed = FeedAPI(self._base_client)
        self.receipts = ReceiptsAPI(self._base_client)
        self.webhooks = WebhooksAPI(self._base_client)

    def __enter__(self) -> "MonzoClient":
        """Context manager entry.

        Returns:
            Self instance
        """
        self._base_client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self._base_client.__exit__(exc_type, exc_val, exc_tb)

    def set_access_token(self, access_token: str) -> None:
        """Set the access token for the client.

        Args:
            access_token: OAuth access token to set
        """
        self._base_client.access_token = access_token

    def whoami(self) -> WhoAmI:
        """Get information about the current access token.

        Returns:
            Information about the current access token
        """
        return self._base_client.whoami()

    @classmethod
    def create_oauth_client(
        cls,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: httpx.Client | None = None,
    ) -> MonzoOAuth:
        """Create OAuth client for authentication.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            http_client: Optional httpx client to use

        Returns:
            OAuth client
        """
        return MonzoOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            http_client=http_client,
        )
