"""Main Monzo API client."""

from typing import Any

import httpx

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
from .core import BaseSyncClient
from .exceptions import MonzoAuthenticationError
from .models import WhoAmI


def _load_cached_token() -> str | None:
    """Load access token from cache, refreshing if expired."""
    try:
        from rich.console import Console

        from .auth import MonzoOAuth
        from .cli import load_env_credentials, load_token_from_cache, try_refresh_token

        # First try to load a valid (non-expired) token
        cached_token = load_token_from_cache()
        if cached_token and isinstance(cached_token, dict):
            access_token = cached_token.get("access_token")
            if isinstance(access_token, str):
                return access_token

        # If no valid token, check for expired token to refresh
        expired_token = load_token_from_cache(include_expired=True)
        if expired_token and isinstance(expired_token, dict):
            # Load OAuth credentials to attempt refresh
            credentials = load_env_credentials()
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            redirect_uri = credentials.get("redirect_uri")

            if client_id and client_secret and redirect_uri:
                # Attempt to refresh the token
                oauth = MonzoOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                )

                # Use a minimal console for refresh output
                console = Console(file=None, quiet=True)

                refreshed_token = try_refresh_token(expired_token, oauth, console)
                if refreshed_token:
                    return refreshed_token

        return None
    except ImportError:
        return None
    except (ImportError, AttributeError, TypeError, ValueError, KeyError):
        return None


class MonzoClient:
    """Main Monzo API client."""

    def __init__(
        self,
        access_token: str | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Monzo client.

        Args:
            access_token: OAuth access token. If not provided, will attempt to
                load from cache.
            http_client: Optional httpx client to use
            timeout: Request timeout in seconds

        Raises:
            MonzoAuthenticationError: If no access token is provided and none can
                be loaded from cache
        """

        if access_token is None:
            access_token = _load_cached_token()
            if access_token is None:
                raise MonzoAuthenticationError(
                    "No access token provided and none found in cache. "
                    "Run 'monzoh-auth' to authenticate first."
                )

        self._base_client = BaseSyncClient(
            access_token=access_token, http_client=http_client, timeout=timeout
        )

        # Initialize API endpoints
        self.accounts = AccountsAPI(self._base_client)
        self.transactions = TransactionsAPI(self._base_client)
        self.pots = PotsAPI(self._base_client)
        self.attachments = AttachmentsAPI(self._base_client)
        self.feed = FeedAPI(self._base_client)
        self.receipts = ReceiptsAPI(self._base_client)
        self.webhooks = WebhooksAPI(self._base_client)

    def __enter__(self) -> "MonzoClient":
        """Context manager entry."""
        self._base_client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self._base_client.__exit__(exc_type, exc_val, exc_tb)

    def whoami(self) -> WhoAmI:
        """Get information about the current access token."""
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
