"""Tests for the main client."""

from typing import Any

import pytest

from monzoh import MonzoClient, MonzoOAuth
from monzoh.exceptions import MonzoBadRequestError


class TestMonzoClient:
    """Test MonzoClient."""

    def test_init(self, mock_http_client: Any) -> None:
        """Test client initialization."""
        client = MonzoClient("test_token", http_client=mock_http_client)
        assert client._base_client.access_token == "test_token"
        assert client._base_client._http_client is mock_http_client

    def test_context_manager(self, mock_http_client: Any) -> None:
        """Test sync context manager."""
        with MonzoClient("test_token", http_client=mock_http_client) as client:
            assert isinstance(client, MonzoClient)

    def test_whoami(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test whoami endpoint."""
        mock_response = mock_response(
            json_data={
                "authenticated": True,
                "client_id": "test_client_id",
                "user_id": "test_user_id",
            }
        )
        monzo_client._base_client._get.return_value = mock_response

        result = monzo_client.whoami()

        assert result.authenticated is True
        assert result.client_id == "test_client_id"
        assert result.user_id == "test_user_id"

    def test_create_oauth_client(self, mock_http_client: Any) -> None:
        """Test OAuth client creation."""
        oauth = MonzoClient.create_oauth_client(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        assert isinstance(oauth, MonzoOAuth)
        assert oauth.client_id == "test_id"
        assert oauth.client_secret == "test_secret"
        assert oauth.redirect_uri == "https://example.com/callback"


class TestOAuthClient:
    """Test OAuth client."""

    def test_init(self, mock_http_client: Any) -> None:
        """Test OAuth client initialization."""
        oauth = MonzoOAuth(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        assert oauth.client_id == "test_id"
        assert oauth.client_secret == "test_secret"
        assert oauth.redirect_uri == "https://example.com/callback"

    def test_get_authorization_url(self, oauth_client: Any) -> None:
        """Test authorization URL generation."""
        url = oauth_client.get_authorization_url(state="test_state")

        assert url.startswith("https://auth.monzo.com/?")
        assert "client_id=test_client_id" in url
        assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
        assert "response_type=code" in url
        assert "state=test_state" in url

    def test_exchange_code_for_token(
        self,
        oauth_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test code exchange for token."""
        mock_response = mock_response(
            json_data={
                "access_token": "access_token",
                "client_id": "test_client_id",
                "expires_in": 21600,
                "refresh_token": "refresh_token",
                "token_type": "Bearer",
                "user_id": "test_user_id",
            }
        )
        mock_http_client.post.return_value = mock_response

        token = oauth_client.exchange_code_for_token("test_code")

        assert token.access_token == "access_token"
        assert token.refresh_token == "refresh_token"
        assert token.user_id == "test_user_id"

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "oauth2/token" in call_args[0][0]
        assert call_args[1]["data"]["code"] == "test_code"

    def test_exchange_code_error(
        self,
        oauth_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test code exchange error handling."""
        mock_response = mock_response(status_code=400)
        mock_http_client.post.return_value = mock_response

        with pytest.raises(MonzoBadRequestError):
            oauth_client.exchange_code_for_token("invalid_code")

    def test_refresh_token(
        self,
        oauth_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test token refresh."""
        mock_response = mock_response(
            json_data={
                "access_token": "new_access_token",
                "client_id": "test_client_id",
                "expires_in": 21600,
                "refresh_token": "new_refresh_token",
                "token_type": "Bearer",
                "user_id": "test_user_id",
            }
        )
        mock_http_client.post.return_value = mock_response

        token = oauth_client.refresh_token("old_refresh_token")

        assert token.access_token == "new_access_token"
        assert token.refresh_token == "new_refresh_token"

    def test_logout(
        self,
        oauth_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test logout."""
        mock_response = mock_response()
        mock_http_client.post.return_value = mock_response

        oauth_client.logout("test_token")

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "oauth2/logout" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
