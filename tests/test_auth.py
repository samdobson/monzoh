"""Tests for auth API."""

from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from monzoh.auth import MonzoOAuth
from monzoh.exceptions import MonzoAuthenticationError, MonzoBadRequestError
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

    def test_context_manager_closes_own_client(self) -> None:
        """Test context manager closes HTTP client if owned."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            with oauth:
                # Access http_client to create it
                _ = oauth.http_client

            # Should close the client on exit
            mock_client.close.assert_called_once()

    def test_context_manager_doesnt_close_provided_client(
        self, mock_http_client: Any
    ) -> None:
        """Test context manager doesn't close provided HTTP client."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        with oauth:
            pass

        # Should not close the provided client
        mock_http_client.close.assert_not_called()

    def test_exchange_code_for_token_http_error(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test exchange_code_for_token with HTTP error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response = mock_response(
            status_code=400,
            json_data={"error": "invalid_request", "error_description": "Invalid code"},
        )
        mock_http_client.post.return_value = mock_response

        with pytest.raises(MonzoBadRequestError):
            oauth.exchange_code_for_token("invalid_code")

    def test_exchange_code_for_token_http_error_no_json(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test exchange_code_for_token with HTTP error and invalid JSON."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response_obj = mock_response(status_code=500)
        mock_response_obj.text = "Internal Server Error"
        mock_response_obj.json.side_effect = ValueError("Invalid JSON")
        mock_http_client.post.return_value = mock_response_obj

        with pytest.raises(
            Exception
        ):  # Should raise some error from create_error_from_response
            oauth.exchange_code_for_token("test_code")

    def test_exchange_code_for_token_network_error(self, mock_http_client: Any) -> None:
        """Test exchange_code_for_token with network error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_http_client.post.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(MonzoAuthenticationError) as exc_info:
            oauth.exchange_code_for_token("test_code")

        assert "Network error during token exchange: Connection failed" in str(
            exc_info.value
        )

    def test_refresh_token_http_error(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test refresh_token with HTTP error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response = mock_response(
            status_code=400,
            json_data={
                "error": "invalid_grant",
                "error_description": "Invalid refresh token",
            },
        )
        mock_http_client.post.return_value = mock_response

        with pytest.raises(MonzoBadRequestError):
            oauth.refresh_token("invalid_refresh_token")

    def test_refresh_token_http_error_no_json(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test refresh_token with HTTP error and invalid JSON."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response_obj = mock_response(status_code=401)
        mock_response_obj.text = "Unauthorized"
        mock_response_obj.json.side_effect = KeyError("No JSON")
        mock_http_client.post.return_value = mock_response_obj

        with pytest.raises(
            Exception
        ):  # Should raise some error from create_error_from_response
            oauth.refresh_token("test_refresh_token")

    def test_refresh_token_network_error(self, mock_http_client: Any) -> None:
        """Test refresh_token with network error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_http_client.post.side_effect = httpx.RequestError("Network timeout")

        with pytest.raises(MonzoAuthenticationError) as exc_info:
            oauth.refresh_token("test_refresh_token")

        assert "Network error during token refresh: Network timeout" in str(
            exc_info.value
        )

    def test_logout_success(self, mock_http_client: Any, mock_response: Any) -> None:
        """Test successful logout."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response = mock_response()
        mock_http_client.post.return_value = mock_response

        # Should not raise any exception
        oauth.logout("test_access_token")

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "oauth2/logout" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_access_token"

    def test_logout_http_error(self, mock_http_client: Any, mock_response: Any) -> None:
        """Test logout with HTTP error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response = mock_response(
            status_code=401,
            json_data={
                "error": "invalid_token",
                "error_description": "Token not found",
            },
        )
        mock_http_client.post.return_value = mock_response

        with pytest.raises(
            Exception
        ):  # Should raise some error from create_error_from_response
            oauth.logout("invalid_token")

    def test_logout_http_error_no_json(
        self, mock_http_client: Any, mock_response: Any
    ) -> None:
        """Test logout with HTTP error and invalid JSON."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_response_obj = mock_response(status_code=500)
        mock_response_obj.text = "Server Error"
        mock_response_obj.json.side_effect = TypeError("JSON error")
        mock_http_client.post.return_value = mock_response_obj

        with pytest.raises(
            Exception
        ):  # Should raise some error from create_error_from_response
            oauth.logout("test_token")

    def test_logout_network_error(self, mock_http_client: Any) -> None:
        """Test logout with network error."""
        oauth = MonzoOAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="https://example.com/callback",
            http_client=mock_http_client,
        )

        mock_http_client.post.side_effect = httpx.RequestError("Connection reset")

        with pytest.raises(MonzoAuthenticationError) as exc_info:
            oauth.logout("test_token")

        assert "Network error during logout: Connection reset" in str(exc_info.value)
