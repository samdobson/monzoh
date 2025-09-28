"""Async Monzo API client."""

import types

import httpx

from .api.async_accounts import AsyncAccountsAPI
from .api.async_attachments import AsyncAttachmentsAPI
from .api.async_feed import AsyncFeedAPI
from .api.async_pots import AsyncPotsAPI
from .api.async_receipts import AsyncReceiptsAPI
from .api.async_transactions import AsyncTransactionsAPI
from .api.async_webhooks import AsyncWebhooksAPI
from .auth import MonzoOAuth
from .core.async_base import BaseAsyncClient
from .core.retry import RetryConfig
from .exceptions import MonzoAuthenticationError
from .models import WhoAmI


def _load_cached_token() -> str | None:
    """Load access token from cache.

    Returns:
        Access token if available, None otherwise
    """
    try:
        from .cli import load_token_from_cache

        cached_token = load_token_from_cache()
        if cached_token and isinstance(cached_token, dict):
            access_token = cached_token.get("access_token")
            return access_token if isinstance(access_token, str) else None
    except ImportError:
        return None
    except (AttributeError, TypeError, ValueError, KeyError):
        return None
    else:
        return None


class AsyncMonzoClient:
    """Async Monzo API client.

    Args:
        access_token: OAuth access token. If not provided, will attempt to
            load from cache.
        http_client: Optional httpx async client to use
        timeout: Request timeout in seconds
        retry_config: Retry configuration for handling transient errors

    Raises:
        MonzoAuthenticationError: If no access token is provided and none can
            be loaded from cache
    """

    def __init__(
        self,
        access_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        retry_config: RetryConfig | None = None,
    ) -> None:
        if access_token is None:
            access_token = _load_cached_token()
            if access_token is None:
                msg = (
                    "No access token provided and none found in cache. "
                    "Run 'monzoh-auth' to authenticate first."
                )
                raise MonzoAuthenticationError(msg)

        self._base_client = BaseAsyncClient(
            access_token=access_token,
            http_client=http_client,
            timeout=timeout,
            retry_config=retry_config,
        )

        self.accounts = AsyncAccountsAPI(self._base_client)
        self.transactions = AsyncTransactionsAPI(self._base_client)
        self.pots = AsyncPotsAPI(self._base_client)
        self.attachments = AsyncAttachmentsAPI(self._base_client)
        self.feed = AsyncFeedAPI(self._base_client)
        self.receipts = AsyncReceiptsAPI(self._base_client)
        self.webhooks = AsyncWebhooksAPI(self._base_client)

    async def __aenter__(self) -> "AsyncMonzoClient":
        """Async context manager entry.

        Returns:
            Self instance
        """
        await self._base_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        await self._base_client.__aexit__(exc_type, exc_val, exc_tb)

    async def whoami(self) -> WhoAmI:
        """Get information about the current access token.

        Returns:
            Information about the current access token
        """
        return await self._base_client.whoami()

    @classmethod
    def create_oauth_client(
        cls,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> MonzoOAuth:
        """Create OAuth client for authentication.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            http_client: Optional httpx async client to use (Note: OAuth flow
                        currently uses sync client internally)

        Returns:
            OAuth client

        Note:
            The OAuth client currently uses sync httpx.Client internally,
            even when an async client is provided. This may be updated
            in a future version.
        """
        sync_http_client = None
        if http_client:
            pass

        return MonzoOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            http_client=sync_http_client,
        )
