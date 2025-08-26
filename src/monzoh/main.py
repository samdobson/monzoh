"""Main Monzo API client."""

from typing import Any

import httpx

from .accounts import AccountsAPI
from .attachments import AttachmentsAPI
from .auth import MonzoOAuth
from .client import BaseSyncClient
from .exceptions import MonzoAuthenticationError
from .feed import FeedAPI
from .models import WhoAmI
from .pots import PotsAPI
from .receipts import ReceiptsAPI
from .transactions import TransactionsAPI
from .webhooks import WebhooksAPI


def _load_cached_token() -> str | None:
    """Load access token from cache."""
    try:
        from .cli import load_token_from_cache

        cached_token = load_token_from_cache()
        if cached_token and isinstance(cached_token, dict):
            access_token = cached_token.get("access_token")
            return access_token if isinstance(access_token, str) else None
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
