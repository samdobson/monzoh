"""Tests for CLI functionality."""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Any
from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from monzoh.cli import (
    OAuthCallbackHandler,
    OAuthCallbackServer,
    authenticate,
    clear_token_cache,
    get_credentials_interactively,
    get_token_cache_path,
    load_env_credentials,
    load_token_from_cache,
    save_credentials_to_env,
    save_token_to_cache,
    start_callback_server,
    try_refresh_token,
)
from monzoh.models import OAuthToken


class TestOAuthCallbackHandler:
    """Tests for OAuth callback handler - basic structure tests only."""

    def test_handler_exists(self) -> None:
        """Test that the handler class exists and can be imported."""
        assert OAuthCallbackHandler is not None


class TestOAuthCallbackServer:
    """Tests for OAuth callback server."""

    def test_init(self) -> None:
        """Test server initialization."""
        server = OAuthCallbackServer(("localhost", 8080))
        assert server.auth_code is None
        assert server.state is None
        assert server.error is None
        assert isinstance(server.callback_received, Event)
        assert not server.callback_received.is_set()


class TestLoadEnvCredentials:
    """Tests for loading environment credentials."""

    def test_load_from_env_variables(self) -> None:
        """Test loading credentials from environment variables."""
        with patch.dict(
            os.environ,
            {
                "MONZO_CLIENT_ID": "test_id",
                "MONZO_CLIENT_SECRET": "test_secret",
                "MONZO_REDIRECT_URI": "http://localhost:3000/callback",
            },
        ):
            creds = load_env_credentials()
            assert creds["client_id"] == "test_id"
            assert creds["client_secret"] == "test_secret"
            assert creds["redirect_uri"] == "http://localhost:3000/callback"

    def test_load_with_defaults(self) -> None:
        """Test loading with default redirect URI."""
        creds = load_env_credentials()
        # At minimum should have redirect_uri default
        assert "redirect_uri" in creds

    @patch("monzoh.cli.load_dotenv")
    @patch("pathlib.Path.exists")
    def test_load_with_dotenv_file(
        self, mock_exists: Any, mock_load_dotenv: Any
    ) -> None:
        """Test loading with .env file."""
        mock_exists.return_value = True

        with patch.dict(os.environ, {"MONZO_CLIENT_ID": "from_env"}):
            creds = load_env_credentials()
            mock_load_dotenv.assert_called_once()
            assert creds["client_id"] == "from_env"


class TestGetCredentialsInteractively:
    """Tests for interactive credential gathering."""

    def test_with_existing_credentials(self) -> None:
        """Test when credentials already exist."""
        console = Console()
        existing_creds: dict[str, str | None] = {
            "client_id": "existing_id",
            "client_secret": "existing_secret",
            "redirect_uri": "http://localhost:8080/callback",
        }

        with patch.object(console, "print"):
            creds = get_credentials_interactively(console, existing_creds)

        assert creds["client_id"] == "existing_id"
        assert creds["client_secret"] == "existing_secret"
        assert creds["redirect_uri"] == "http://localhost:8080/callback"

    @patch("monzoh.cli.Prompt.ask")
    def test_with_missing_credentials(self, mock_prompt: Any) -> None:
        """Test when credentials need to be prompted."""
        console = Console()
        existing_creds: dict[str, str | None] = {
            "client_id": None,
            "client_secret": None,
            "redirect_uri": None,
        }

        mock_prompt.side_effect = ["new_id", "new_secret"]

        with patch.object(console, "print"):
            creds = get_credentials_interactively(console, existing_creds)

        assert creds["client_id"] == "new_id"
        assert creds["client_secret"] == "new_secret"
        assert creds["redirect_uri"] == "http://localhost:8080/callback"


class TestStartCallbackServer:
    """Tests for callback server startup."""

    @patch("monzoh.cli.Thread")
    @patch("monzoh.cli.OAuthCallbackServer")
    def test_start_callback_server(
        self, mock_server_class: Any, mock_thread: Any
    ) -> None:
        """Test starting callback server."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        result = start_callback_server(3000)

        mock_server_class.assert_called_once_with(("localhost", 3000))
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert result == mock_server


class TestSaveCredentialsToEnv:
    """Tests for saving credentials to .env file."""

    def test_save_to_new_file(self) -> None:
        """Test saving credentials to new .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            console = Console()
            creds = {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            with (
                patch("monzoh.cli.Confirm.ask", return_value=True),
                patch.object(console, "print"),
            ):
                save_credentials_to_env(creds, console)

            env_path = Path(".env")
            assert env_path.exists()

            content = env_path.read_text()
            assert "MONZO_CLIENT_ID=test_id" in content
            assert "MONZO_CLIENT_SECRET=test_secret" in content
            assert "MONZO_REDIRECT_URI=http://localhost:8080/callback" in content

    def test_save_to_existing_file(self) -> None:
        """Test saving credentials to existing .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            env_path = Path(".env")
            env_path.write_text("EXISTING_VAR=value\nMONZO_CLIENT_ID=old_id\n")

            console = Console()
            creds = {
                "client_id": "new_id",
                "client_secret": "new_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            with (
                patch("monzoh.cli.Confirm.ask", return_value=True),
                patch.object(console, "print"),
            ):
                save_credentials_to_env(creds, console)

            content = env_path.read_text()
            assert "EXISTING_VAR=value" in content
            assert "MONZO_CLIENT_ID=new_id" in content
            assert "old_id" not in content

    def test_save_function_exists(self) -> None:
        """Test that save function exists."""
        assert save_credentials_to_env is not None


class TestTokenCache:
    """Tests for token caching functionality."""

    def test_get_token_cache_path_basic(self) -> None:
        """Test getting cache path."""
        with patch("platform.system", return_value="Darwin"):
            path = get_token_cache_path()
            assert str(path).endswith("monzoh/tokens.json")

    def test_save_token_to_cache(self) -> None:
        """Test saving token to cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            token = OAuthToken(
                access_token="test_access",
                token_type="Bearer",
                expires_in=3600,
                refresh_token="test_refresh",
                user_id="user123",
                client_id="client123",
            )
            console = Console()

            with (
                patch("monzoh.cli.get_token_cache_path", return_value=cache_path),
                patch.object(console, "print"),
            ):
                save_token_to_cache(token, console)

            assert cache_path.exists()

            with open(cache_path) as f:
                data = json.load(f)

            assert data["access_token"] == "test_access"
            assert data["refresh_token"] == "test_refresh"
            assert data["user_id"] == "user123"
            assert "expires_at" in data

    def test_save_token_to_cache_error(self) -> None:
        """Test error handling when saving token to cache."""
        token = OAuthToken(
            access_token="test_access",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test_refresh",
            user_id="user123",
            client_id="client123",
        )
        console = Console()

        with (
            patch(
                "monzoh.cli.get_token_cache_path",
                side_effect=Exception("Permission denied"),
            ),
            patch.object(console, "print") as mock_print,
        ):
            save_token_to_cache(token, console)
            # Should print warning but not raise
            mock_print.assert_called()

    def test_load_token_from_cache_valid(self) -> None:
        """Test loading valid token from cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            # Create cache with future expiry
            expires_at = datetime.now() + timedelta(hours=1)
            cache_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_at": expires_at.isoformat(),
                "user_id": "user123",
                "client_id": "client123",
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            with patch("monzoh.cli.get_token_cache_path", return_value=cache_path):
                result = load_token_from_cache()

            assert result is not None
            assert result["access_token"] == "test_access"

    def test_load_token_from_cache_expired(self) -> None:
        """Test loading expired token from cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            # Create cache with past expiry
            expires_at = datetime.now() - timedelta(hours=1)
            cache_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_at": expires_at.isoformat(),
                "user_id": "user123",
                "client_id": "client123",
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            with patch("monzoh.cli.get_token_cache_path", return_value=cache_path):
                result = load_token_from_cache()

            assert result is None

    def test_load_token_from_cache_missing(self) -> None:
        """Test loading token when cache file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "nonexistent.json"

            with patch("monzoh.cli.get_token_cache_path", return_value=cache_path):
                result = load_token_from_cache()

            assert result is None

    def test_clear_token_cache(self) -> None:
        """Test clearing token cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"
            cache_path.write_text('{"test": "data"}')

            with patch("monzoh.cli.get_token_cache_path", return_value=cache_path):
                clear_token_cache()

            assert not cache_path.exists()

    def test_clear_token_cache_missing_file(self) -> None:
        """Test clearing cache when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "nonexistent.json"

            with patch("monzoh.cli.get_token_cache_path", return_value=cache_path):
                # Should not raise exception
                clear_token_cache()


class TestTryRefreshToken:
    """Tests for token refresh functionality."""

    def test_refresh_token_success(self) -> None:
        """Test successful token refresh."""
        cached_token = {"refresh_token": "test_refresh"}
        oauth_mock = Mock()
        console = Console()

        new_token = OAuthToken(
            access_token="new_access",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="new_refresh",
            user_id="user123",
            client_id="client123",
        )
        oauth_mock.refresh_token.return_value = new_token
        oauth_mock.__enter__ = Mock(return_value=oauth_mock)
        oauth_mock.__exit__ = Mock(return_value=None)

        with patch("monzoh.cli.save_token_to_cache"), patch.object(console, "print"):
            result = try_refresh_token(cached_token, oauth_mock, console)

        assert result == "new_access"
        oauth_mock.refresh_token.assert_called_once_with("test_refresh")

    def test_refresh_token_failure(self) -> None:
        """Test failed token refresh."""
        cached_token = {"refresh_token": "test_refresh"}
        oauth_mock = Mock()
        console = Console()

        oauth_mock.refresh_token.side_effect = Exception("Refresh failed")
        oauth_mock.__enter__ = Mock(return_value=oauth_mock)
        oauth_mock.__exit__ = Mock(return_value=None)

        with (
            patch("monzoh.cli.clear_token_cache") as mock_clear,
            patch.object(console, "print"),
        ):
            result = try_refresh_token(cached_token, oauth_mock, console)

        assert result is None
        mock_clear.assert_called_once()

    def test_refresh_token_no_refresh_token(self) -> None:
        """Test refresh when no refresh token available."""
        cached_token: dict[str, Any] = {}
        oauth_mock = Mock()
        console = Console()

        result = try_refresh_token(cached_token, oauth_mock, console)

        assert result is None
        oauth_mock.refresh_token.assert_not_called()


class TestAuthenticate:
    """Tests for main authentication flow."""

    @patch("monzoh.cli.MonzoClient")
    @patch("monzoh.cli.load_token_from_cache")
    def test_authenticate_with_valid_cached_token(
        self, mock_load_cache: Any, mock_client_class: Any
    ) -> None:
        """Test authentication with valid cached token."""
        # Mock cached token
        cached_token = {"access_token": "cached_token", "user_id": "user123"}
        mock_load_cache.return_value = cached_token

        # Mock client and whoami response
        mock_client = Mock()
        mock_whoami = Mock()
        mock_whoami.user_id = "user123"
        mock_client.whoami.return_value = mock_whoami
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        with patch("monzoh.cli.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            result = authenticate()

            assert result == "cached_token"
            mock_client_class.assert_called_once_with("cached_token")
            mock_client.whoami.assert_called_once()

    @patch("monzoh.cli.load_token_from_cache")
    def test_authenticate_no_cached_token(self, mock_load_cache: Any) -> None:
        """Test authentication without cached token."""
        mock_load_cache.return_value = None

        with (
            patch("monzoh.cli.Console") as mock_console_class,
            patch("monzoh.cli.load_env_credentials") as mock_load_env,
            patch("monzoh.cli.get_credentials_interactively") as mock_get_creds,
            patch("monzoh.cli.save_credentials_to_env"),
            patch("monzoh.cli.start_callback_server") as mock_start_server,
            patch("monzoh.cli.MonzoOAuth") as mock_oauth_class,
            patch("monzoh.cli.secrets.token_urlsafe") as mock_token,
            patch("monzoh.cli.webbrowser.open"),
            patch("monzoh.cli.MonzoClient") as mock_client_class,
        ):
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            mock_load_env.return_value = {"client_id": None, "client_secret": None}
            mock_get_creds.return_value = {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            # Mock server
            mock_server = Mock()
            mock_server.callback_received = Mock()
            mock_server.callback_received.wait.return_value = True
            mock_server.error = None
            mock_server.auth_code = "test_code"
            mock_server.state = "test_state"
            mock_start_server.return_value = mock_server

            # Mock OAuth
            mock_oauth = Mock()
            mock_oauth_class.return_value = mock_oauth
            mock_oauth.__enter__ = Mock(return_value=mock_oauth)
            mock_oauth.__exit__ = Mock(return_value=None)
            mock_oauth.get_authorization_url.return_value = "http://auth.url"

            mock_token.return_value = "test_state"

            # Mock token response
            mock_oauth_token = Mock()
            mock_oauth_token.access_token = "new_access_token"
            mock_oauth.exchange_code_for_token.return_value = mock_oauth_token

            # Mock client
            mock_client = Mock()
            mock_whoami = Mock()
            mock_whoami.user_id = "user123"
            mock_client.whoami.return_value = mock_whoami
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=None)
            mock_client_class.return_value = mock_client

            with patch("monzoh.cli.save_token_to_cache"):
                result = authenticate()

            assert result == "new_access_token"

    @patch("monzoh.cli.load_token_from_cache")
    def test_authenticate_keyboard_interrupt(self, mock_load_cache: Any) -> None:
        """Test authentication cancelled by keyboard interrupt."""
        mock_load_cache.side_effect = KeyboardInterrupt()

        result = authenticate()
        assert result is None

    @patch("monzoh.cli.load_token_from_cache")
    def test_authenticate_timeout(self, mock_load_cache: Any) -> None:
        """Test authentication timeout."""
        mock_load_cache.return_value = None

        with (
            patch("monzoh.cli.Console") as mock_console_class,
            patch("monzoh.cli.load_env_credentials") as mock_load_env,
            patch("monzoh.cli.get_credentials_interactively") as mock_get_creds,
            patch("monzoh.cli.save_credentials_to_env"),
            patch("monzoh.cli.start_callback_server") as mock_start_server,
            patch("monzoh.cli.MonzoOAuth") as mock_oauth_class,
            patch("monzoh.cli.secrets.token_urlsafe"),
            patch("monzoh.cli.webbrowser.open"),
        ):
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            mock_load_env.return_value = {"client_id": None, "client_secret": None}
            mock_get_creds.return_value = {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            # Mock server with timeout
            mock_server = Mock()
            mock_server.callback_received = Mock()
            mock_server.callback_received.wait.return_value = False  # Timeout
            mock_start_server.return_value = mock_server

            mock_oauth = Mock()
            mock_oauth_class.return_value = mock_oauth
            mock_oauth.get_authorization_url.return_value = "http://auth.url"

            result = authenticate()
            assert result is None


@patch("monzoh.cli.authenticate")
def test_main_success(mock_authenticate: Any) -> None:
    """Test main function with successful authentication."""
    mock_authenticate.return_value = "test_token"

    with patch("builtins.print") as mock_print:
        from monzoh.cli import main

        main()
        mock_print.assert_called()


@patch("monzoh.cli.authenticate")
def test_main_failure(mock_authenticate: Any) -> None:
    """Test main function with failed authentication."""
    mock_authenticate.return_value = None

    with patch("builtins.print"), pytest.raises(SystemExit):
        from monzoh.cli import main

        main()


@patch("monzoh.cli.authenticate")
def test_main_keyboard_interrupt(mock_authenticate: Any) -> None:
    """Test main function with keyboard interrupt."""
    mock_authenticate.side_effect = KeyboardInterrupt()

    with patch("builtins.print"), pytest.raises(SystemExit):
        from monzoh.cli import main

        main()
