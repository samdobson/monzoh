"""Tests for main.py functionality."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from monzoh.client import MonzoClient, _load_cached_token
from monzoh.exceptions import MonzoAuthenticationError


class TestLoadCachedToken:
    """Tests for _load_cached_token function."""

    def test_load_cached_token_import_error(self) -> None:
        """Test when CLI module cannot be imported."""
        with patch.dict("sys.modules", {"monzoh.cli": None}):
            result = _load_cached_token()
            assert result is None


class TestMonzoClient:
    """Tests for MonzoClient main functionality."""

    def test_init_with_token(self, mock_http_client: Any) -> None:
        """Test initialization with provided token.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        client = MonzoClient("test_token", http_client=mock_http_client)

        assert client._base_client.access_token == "test_token"
        assert hasattr(client, "accounts")
        assert hasattr(client, "transactions")
        assert hasattr(client, "pots")
        assert hasattr(client, "attachments")
        assert hasattr(client, "feed")
        assert hasattr(client, "receipts")
        assert hasattr(client, "webhooks")

    @patch("monzoh.client._load_cached_token")
    def test_init_without_token_cached_available(
        self, mock_load_token: Any, mock_http_client: Any
    ) -> None:
        """Test initialization without token when cached token is available.

        Args:
            mock_load_token: Mock load token function fixture.
            mock_http_client: Mock HTTP client fixture.
        """
        mock_load_token.return_value = "cached_token"

        client = MonzoClient(http_client=mock_http_client)

        assert client._base_client.access_token == "cached_token"
        mock_load_token.assert_called_once()

    @patch("monzoh.client._load_cached_token")
    def test_init_without_token_no_cache(
        self, mock_load_token: Any, mock_http_client: Any
    ) -> None:
        """Test initialization without token when no cached token is available.

        Args:
            mock_load_token: Mock load token function fixture.
            mock_http_client: Mock HTTP client fixture.
        """
        mock_load_token.return_value = None

        client = MonzoClient(http_client=mock_http_client)

        assert client._base_client.access_token is None

        with pytest.raises(MonzoAuthenticationError, match="Access token is not set"):
            client.whoami()

    @patch("monzoh.client._load_cached_token")
    def test_set_access_token(
        self, mock_load_token: Any, mock_http_client: Any
    ) -> None:
        """Test setting access token after client creation.

        Args:
            mock_load_token: Mock load token function fixture.
            mock_http_client: Mock HTTP client fixture.
        """
        mock_load_token.return_value = None

        client = MonzoClient(http_client=mock_http_client)
        assert client._base_client.access_token is None

        client.set_access_token("new_token")
        assert client._base_client.access_token == "new_token"

    def test_init_with_custom_timeout(self, mock_http_client: Any) -> None:
        """Test initialization with custom timeout.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        client = MonzoClient("test_token", http_client=mock_http_client, timeout=60.0)

        assert client._base_client._timeout == 60.0

    def test_context_manager(self, mock_http_client: Any) -> None:
        """Test context manager functionality.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        client = MonzoClient("test_token", http_client=mock_http_client)

        with (
            patch.object(client._base_client, "__enter__") as mock_enter,
            patch.object(client._base_client, "__exit__") as mock_exit,
        ):
            with client as ctx_client:
                assert ctx_client is client
                mock_enter.assert_called_once()

            mock_exit.assert_called_once()

    def test_whoami(self, mock_http_client: Any) -> None:
        """Test whoami method.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        client = MonzoClient("test_token", http_client=mock_http_client)

        mock_whoami_result = Mock()
        with patch.object(client._base_client, "whoami") as mock_whoami:
            mock_whoami.return_value = mock_whoami_result

            result = client.whoami()

            assert result is mock_whoami_result
            mock_whoami.assert_called_once()

    def test_create_oauth_client(self) -> None:
        """Test create_oauth_client class method."""
        from monzoh.auth import MonzoOAuth

        mock_http_client = Mock()
        oauth_client = MonzoClient.create_oauth_client(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        assert isinstance(oauth_client, MonzoOAuth)
        assert oauth_client.client_id == "test_id"
        assert oauth_client.client_secret == "test_secret"
        assert oauth_client.redirect_uri == "https://example.com/callback"
        assert oauth_client._http_client is mock_http_client

    def test_create_oauth_client_without_http_client(self) -> None:
        """Test create_oauth_client without HTTP client."""
        from monzoh.auth import MonzoOAuth

        oauth_client = MonzoClient.create_oauth_client(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
        )

        assert isinstance(oauth_client, MonzoOAuth)
        assert oauth_client.client_id == "test_id"
        assert oauth_client.client_secret == "test_secret"
        assert oauth_client.redirect_uri == "https://example.com/callback"
        assert oauth_client._http_client is None

    def test_api_endpoints_initialization(self, mock_http_client: Any) -> None:
        """Test that all API endpoints are properly initialized.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        from monzoh.api.accounts import AccountsAPI
        from monzoh.api.attachments import AttachmentsAPI
        from monzoh.api.feed import FeedAPI
        from monzoh.api.pots import PotsAPI
        from monzoh.api.receipts import ReceiptsAPI
        from monzoh.api.transactions import TransactionsAPI
        from monzoh.api.webhooks import WebhooksAPI

        client = MonzoClient("test_token", http_client=mock_http_client)

        assert isinstance(client.accounts, AccountsAPI)
        assert isinstance(client.transactions, TransactionsAPI)
        assert isinstance(client.pots, PotsAPI)
        assert isinstance(client.attachments, AttachmentsAPI)
        assert isinstance(client.feed, FeedAPI)
        assert isinstance(client.receipts, ReceiptsAPI)
        assert isinstance(client.webhooks, WebhooksAPI)
