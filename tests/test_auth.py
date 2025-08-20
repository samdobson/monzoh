"""Tests for auth API."""

from typing import Any

from monzoh.auth import MonzoOAuth
from monzoh.models import OAuthToken


class TestMonzoOAuth:
    """Test MonzoOAuth."""

    def test_init(self, mock_http_client: Any) -> None:
        """Test OAuth client initialization."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )
        assert oauth.client_id == "test_client_id"
        assert oauth.client_secret == "test_client_secret"
        assert oauth.redirect_uri == "https://example.com/callback"
        assert oauth._http_client is mock_http_client
        assert oauth._own_client is False

    def test_init_without_http_client(self) -> None:
        """Test OAuth client initialization without http_client."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )
        assert oauth.client_id == "test_client_id"
        assert oauth.client_secret == "test_client_secret"
        assert oauth.redirect_uri == "https://example.com/callback"
        assert oauth._http_client is None
        assert oauth._own_client is True

    def test_http_client_property(self, mock_http_client: Any) -> None:
        """Test http_client property."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )
        assert oauth.http_client is mock_http_client

    def test_http_client_property_lazy_creation(self) -> None:
        """Test http_client property creates client if none provided."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )
        # First call should create client
        client1 = oauth.http_client
        assert client1 is not None
        # Second call should return same client
        client2 = oauth.http_client
        assert client1 is client2

    def test_context_manager(self, mock_http_client: Any) -> None:
        """Test sync context manager."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )
        with oauth as client:
            assert client is oauth

    def test_get_authorization_url(self, mock_http_client: Any) -> None:
        """Test get_authorization_url method."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        url = oauth.get_authorization_url()

        assert url.startswith("https://auth.monzo.com/")
        assert "client_id=test_client_id" in url
        assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in url
        assert "response_type=code" in url

    def test_get_authorization_url_with_state(self, mock_http_client: Any) -> None:
        """Test get_authorization_url method with state."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        url = oauth.get_authorization_url(state="test_state")

        assert "state=test_state" in url

    def test_exchange_code_for_token(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test exchange_code_for_token method."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        token_data = {
            "access_token": "access_token_123",
            "client_id": "test_client_id",
            "expires_in": 21600,
            "refresh_token": "refresh_token_123",
            "token_type": "Bearer",
            "user_id": "user_123",
        }
        mock_response = mock_response(json_data=token_data)
        mock_http_client.post.return_value = mock_response

        token = oauth.exchange_code_for_token("auth_code_123")

        assert isinstance(token, OAuthToken)
        assert token.access_token == "access_token_123"
        assert token.refresh_token == "refresh_token_123"
        assert token.user_id == "user_123"

    def test_refresh_token(self, mock_http_client: Any, mock_response: Any) -> None:
        """Test refresh_token method."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        token_data = {
            "access_token": "new_access_token_123",
            "client_id": "test_client_id",
            "expires_in": 21600,
            "refresh_token": "new_refresh_token_123",
            "token_type": "Bearer",
            "user_id": "user_123",
        }
        mock_response = mock_response(json_data=token_data)
        mock_http_client.post.return_value = mock_response

        token = oauth.refresh_token("old_refresh_token_123")

        assert isinstance(token, OAuthToken)
        assert token.access_token == "new_access_token_123"
        assert token.refresh_token == "new_refresh_token_123"
        assert token.user_id == "user_123"
