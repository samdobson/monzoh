"""Tests for the main client."""

from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from monzoh import MonzoClient, MonzoOAuth
from monzoh.core.base import BaseSyncClient, MockResponse
from monzoh.exceptions import MonzoBadRequestError, MonzoError, MonzoNetworkError


class TestMonzoClient:
    """Test MonzoClient."""

    def test_init(self, mock_http_client: Any) -> None:
        """Test client initialization.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        client = MonzoClient("test_token", http_client=mock_http_client)
        assert client._base_client.access_token == "test_token"
        assert client._base_client._http_client is mock_http_client

    def test_context_manager(self, mock_http_client: Any) -> None:
        """Test sync context manager.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
        with MonzoClient("test_token", http_client=mock_http_client) as client:
            assert isinstance(client, MonzoClient)

    def test_whoami(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test whoami endpoint.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
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
        """Test OAuth client creation.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
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
        """Test OAuth client initialization.

        Args:
            mock_http_client: Mock HTTP client fixture.
        """
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
        """Test authorization URL generation.

        Args:
            oauth_client: OAuth client fixture.
        """
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
        """Test code exchange for token.

        Args:
            oauth_client: OAuth client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
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
        """Test code exchange error handling.

        Args:
            oauth_client: OAuth client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
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
        """Test token refresh.

        Args:
            oauth_client: OAuth client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
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
        """Test logout.

        Args:
            oauth_client: OAuth client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response()
        mock_http_client.post.return_value = mock_response

        oauth_client.logout("test_token")

        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert "oauth2/logout" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"


class TestMockResponse:
    """Test MockResponse class."""

    def test_init(self) -> None:
        """Test MockResponse initialization."""
        json_data = {"test": "data"}
        response = MockResponse(json_data, status_code=201)

        assert response._json_data == json_data
        assert response.status_code == 201
        assert response.text == '{"test": "data"}'
        assert response.headers == {}
        assert response.cookies == {}
        assert response.url == ""
        assert response.request is None

    def test_init_default_status(self) -> None:
        """Test MockResponse with default status code."""
        json_data = {"test": "data"}
        response = MockResponse(json_data)

        assert response.status_code == 200

    def test_json_method(self) -> None:
        """Test json method returns correct data."""
        json_data = {"key": "value", "number": 123}
        response = MockResponse(json_data)

        assert response.json() == json_data

    def test_raise_for_status_success(self) -> None:
        """Test raise_for_status with successful status code."""
        response = MockResponse({}, status_code=200)
        response.raise_for_status()

    def test_raise_for_status_error(self) -> None:
        """Test raise_for_status with error status code."""
        response = MockResponse({}, status_code=400)

        with pytest.raises(MonzoError) as exc_info:
            response.raise_for_status()

        assert "HTTP 400 error" in str(exc_info.value)


class TestBaseSyncClient:
    """Test BaseSyncClient class."""

    def test_init_with_http_client(self) -> None:
        """Test initialization with provided HTTP client."""
        mock_client = Mock()
        client = BaseSyncClient("test_token", http_client=mock_client, timeout=60.0)

        assert client.access_token == "test_token"
        assert client._http_client is mock_client
        assert client._own_client is False
        assert client._timeout == 60.0

    def test_init_without_http_client(self) -> None:
        """Test initialization without HTTP client."""
        client = BaseSyncClient("test_token")

        assert client.access_token == "test_token"
        assert client._http_client is None
        assert client._own_client is True
        assert client._timeout == 30.0

    def test_http_client_property_creates_client(self) -> None:
        """Test http_client property creates client when needed."""
        client = BaseSyncClient("test_token")

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            result = client.http_client

            assert result is mock_client
            assert client._http_client is mock_client
            mock_client_class.assert_called_once_with(
                timeout=30.0, headers={"User-Agent": "monzoh-python-client"}
            )

    def test_http_client_property_returns_existing(self) -> None:
        """Test http_client property returns existing client."""
        mock_client = Mock()
        client = BaseSyncClient("test_token", http_client=mock_client)

        result = client.http_client
        assert result is mock_client

    def test_auth_headers(self) -> None:
        """Test auth_headers property."""
        client = BaseSyncClient("my_token")
        headers = client.auth_headers

        assert headers == {"Authorization": "Bearer my_token"}

    def test_is_mock_mode_true(self) -> None:
        """Test is_mock_mode when using test token."""
        client = BaseSyncClient("test")
        assert client.is_mock_mode is True

    def test_is_mock_mode_false(self) -> None:
        """Test is_mock_mode when using real token."""
        client = BaseSyncClient("real_token")
        assert client.is_mock_mode is False

    def test_context_manager_with_own_client(self) -> None:
        """Test context manager when client owns HTTP client."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            client = BaseSyncClient("test_token")

            with client as ctx_client:
                assert ctx_client is client
                _ = ctx_client.http_client

            mock_client.close.assert_called_once()

    def test_context_manager_without_own_client(self) -> None:
        """Test context manager when client doesn't own HTTP client."""
        mock_client = Mock()
        client = BaseSyncClient("test_token", http_client=mock_client)

        with client as ctx_client:
            assert ctx_client is client

        mock_client.close.assert_not_called()

    def test_request_mock_mode(self) -> None:
        """Test _request method in mock mode."""
        client = BaseSyncClient("test")

        with patch("monzoh.core.base.get_mock_response") as mock_get_response:
            mock_data = {"mocked": True}
            mock_get_response.return_value = mock_data

            response = client._request("GET", "/test")

            assert isinstance(response, MockResponse)
            assert response.json() == mock_data
            mock_get_response.assert_called_once_with(
                "/test", "GET", params=None, data=None, json_data=None
            )

    def test_request_real_mode_success(self) -> None:
        """Test _request method in real mode with success."""
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_http_client.request.return_value = mock_response

        client = BaseSyncClient("real_token", http_client=mock_http_client)

        response = client._request(
            "POST",
            "/test",
            params={"param": "value"},
            data={"key": "value"},
            json_data={"json": "data"},
            files={"file": "content"},
            headers={"Custom": "Header"},
        )

        assert response is mock_response

        mock_http_client.request.assert_called_once_with(
            method="POST",
            url="https://api.monzo.com/test",
            params={"param": "value"},
            data={"key": "value"},
            json={"json": "data"},
            files={"file": "content"},
            headers={"Authorization": "Bearer real_token", "Custom": "Header"},
        )

    def test_request_real_mode_http_error(self) -> None:
        """Test _request method with HTTP error status."""
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {"error": "invalid_request"}
        mock_http_client.request.return_value = mock_response

        client = BaseSyncClient("real_token", http_client=mock_http_client)

        with pytest.raises(MonzoBadRequestError):
            client._request("GET", "/test")

    def test_request_real_mode_http_error_no_json(self) -> None:
        """Test _request method with HTTP error and invalid JSON."""
        mock_http_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_http_client.request.return_value = mock_response

        client = BaseSyncClient("real_token", http_client=mock_http_client)

        with pytest.raises(MonzoError):
            client._request("GET", "/test")

    def test_request_network_error(self) -> None:
        """Test _request method with network error."""
        mock_http_client = Mock()
        mock_http_client.request.side_effect = httpx.RequestError("Connection failed")

        client = BaseSyncClient("real_token", http_client=mock_http_client)

        with pytest.raises(MonzoNetworkError):
            client._request("GET", "/test")

    def test_convenience_methods(self) -> None:
        """Test HTTP convenience methods."""
        client = BaseSyncClient("test")

        with patch.object(client, "_request") as mock_request:
            mock_response = Mock()
            mock_request.return_value = mock_response

            result = client._get("/test", params={"p": "v"}, headers={"h": "v"})
            assert result is mock_response
            mock_request.assert_called_with(
                "GET", "/test", params={"p": "v"}, headers={"h": "v"}
            )

            result = client._post(
                "/test",
                data={"d": "v"},
                json_data={"j": "v"},
                files={"f": "v"},
                headers={"h": "v"},
            )
            assert result is mock_response
            mock_request.assert_called_with(
                "POST",
                "/test",
                data={"d": "v"},
                json_data={"j": "v"},
                files={"f": "v"},
                headers={"h": "v"},
            )

            result = client._put(
                "/test", data={"d": "v"}, json_data={"j": "v"}, headers={"h": "v"}
            )
            assert result is mock_response
            mock_request.assert_called_with(
                "PUT",
                "/test",
                data={"d": "v"},
                json_data={"j": "v"},
                headers={"h": "v"},
            )

            result = client._patch("/test", data={"d": "v"}, headers={"h": "v"})
            assert result is mock_response
            mock_request.assert_called_with(
                "PATCH", "/test", data={"d": "v"}, headers={"h": "v"}
            )

            result = client._delete("/test", params={"p": "v"}, headers={"h": "v"})
            assert result is mock_response
            mock_request.assert_called_with(
                "DELETE", "/test", params={"p": "v"}, headers={"h": "v"}
            )

    def test_prepare_expand_params_none(self) -> None:
        """Test _prepare_expand_params with None."""
        client = BaseSyncClient("test")
        result = client._prepare_expand_params(None)
        assert result is None

    def test_prepare_expand_params_empty(self) -> None:
        """Test _prepare_expand_params with empty list."""
        client = BaseSyncClient("test")
        result = client._prepare_expand_params([])
        assert result is None

    def test_prepare_expand_params_with_fields(self) -> None:
        """Test _prepare_expand_params with fields."""
        client = BaseSyncClient("test")
        result = client._prepare_expand_params(["field1", "field2"])

        expected = [("expand[]", "field1"), ("expand[]", "field2")]
        assert result == expected

    def test_prepare_pagination_params_all_none(self) -> None:
        """Test _prepare_pagination_params with all None values."""
        client = BaseSyncClient("test")
        result = client._prepare_pagination_params()
        assert result == {}

    def test_prepare_pagination_params_with_values(self) -> None:
        """Test _prepare_pagination_params with values."""
        client = BaseSyncClient("test")
        result = client._prepare_pagination_params(
            limit=50, since="2023-01-01", before="2023-12-31"
        )

        expected = {"limit": "50", "since": "2023-01-01", "before": "2023-12-31"}
        assert result == expected

    def test_prepare_pagination_params_partial(self) -> None:
        """Test _prepare_pagination_params with partial values."""
        client = BaseSyncClient("test")
        result = client._prepare_pagination_params(limit=25, since="2023-01-01")

        expected = {"limit": "25", "since": "2023-01-01"}
        assert result == expected


class TestClientTokenLoading:
    """Test token loading functionality in client.py."""

    @patch("monzoh.cli.load_token_from_cache")
    def test_load_cached_token_success(self, mock_load_token: Mock) -> None:
        """Test successful token loading from cache."""
        mock_load_token.return_value = {"access_token": "cached_token"}

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result == "cached_token"

    @patch("monzoh.cli.load_token_from_cache")
    def test_load_cached_token_invalid_token(self, mock_load_token: Mock) -> None:
        """Test token loading with invalid token format."""
        mock_load_token.return_value = {"invalid": "format"}

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result is None

    @patch("monzoh.cli.load_token_from_cache")
    @patch("monzoh.cli.load_env_credentials")
    @patch("monzoh.cli.try_refresh_token")
    @patch("monzoh.client.MonzoOAuth")
    @patch("rich.console.Console")
    def test_load_cached_token_refresh_attempt(
        self,
        mock_console_class: Mock,
        mock_oauth_class: Mock,
        mock_refresh: Mock,
        mock_credentials: Mock,
        mock_load_token: Mock,
    ) -> None:
        """Test token refresh attempt when current token is None."""
        mock_load_token.side_effect = [
            None,
            {"refresh_token": "expired_refresh"},
        ]
        mock_credentials.return_value = {
            "client_id": "test_id",
            "client_secret": "test_secret",
            "redirect_uri": "test_uri",
        }
        mock_oauth_instance = Mock()
        mock_oauth_class.return_value = mock_oauth_instance
        mock_refresh.return_value = "refreshed_token"

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result == "refreshed_token"

    @patch("monzoh.cli.load_token_from_cache")
    @patch("monzoh.cli.load_env_credentials")
    def test_load_cached_token_no_credentials(
        self, mock_credentials: Mock, mock_load_token: Mock
    ) -> None:
        """Test token refresh when credentials are missing."""
        mock_load_token.side_effect = [
            None,
            {"refresh_token": "expired_refresh"},
        ]
        mock_credentials.return_value = {}

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result is None

    @patch("monzoh.cli.load_token_from_cache")
    def test_load_cached_token_import_error(self, mock_load_token: Mock) -> None:
        """Test token loading with import error."""
        mock_load_token.side_effect = ImportError("Module not found")

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result is None

    @patch("monzoh.cli.load_token_from_cache")
    def test_load_cached_token_other_exceptions(self, mock_load_token: Mock) -> None:
        """Test token loading with various exceptions."""
        mock_load_token.side_effect = ValueError("Invalid value")

        from monzoh.client import _load_cached_token

        result = _load_cached_token()
        assert result is None

    @patch("monzoh.client._load_cached_token")
    def test_client_initialization_with_cached_token(self, mock_load: Mock) -> None:
        """Test client initialization loads cached token when none provided."""
        mock_load.return_value = "cached_token"

        client = MonzoClient()
        assert client._base_client.access_token == "cached_token"

    @patch("monzoh.client._load_cached_token")
    def test_client_initialization_prefers_provided_token(
        self, mock_load: Mock
    ) -> None:
        """Test client initialization prefers provided token over cached."""
        mock_load.return_value = "cached_token"

        client = MonzoClient(access_token="provided_token")
        assert client._base_client.access_token == "provided_token"
        mock_load.assert_not_called()

    def test_client_set_access_token(self) -> None:
        """Test setting access token on client."""
        client = MonzoClient(access_token="initial_token")
        client.set_access_token("new_token")
        assert client._base_client.access_token == "new_token"
