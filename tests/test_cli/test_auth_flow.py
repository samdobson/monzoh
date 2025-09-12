"""Tests for CLI authentication flow functionality."""

from unittest.mock import Mock, patch

from monzoh.cli import main
from monzoh.cli.auth_flow import authenticate


class TestAuthenticate:
    """Tests for main authentication flow."""

    @patch("monzoh.cli.auth_flow.MonzoClient")
    @patch("monzoh.cli.auth_flow.load_token_from_cache")
    def test_authenticate_with_valid_cached_token(
        self, mock_load_cache: Mock, mock_client_class: Mock
    ) -> None:
        """Test authentication with valid cached token.

        Args:
            mock_load_cache: Mock load cache fixture.
            mock_client_class: Mock client class fixture.
        """
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

        with patch("monzoh.cli.auth_flow.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            result = authenticate()

            assert result == "cached_token"
            mock_client_class.assert_called_once_with("cached_token")
            mock_client.whoami.assert_called_once()

    @patch("monzoh.cli.auth_flow.load_token_from_cache")
    def test_authenticate_no_cached_token(self, mock_load_cache: Mock) -> None:
        """Test authentication without cached token.

        Args:
            mock_load_cache: Mock load cache fixture.
        """
        mock_load_cache.return_value = None

        with (
            patch("monzoh.cli.auth_flow.Console") as mock_console_class,
            patch("monzoh.cli.auth_flow.load_env_credentials") as mock_load_env,
            patch(
                "monzoh.cli.auth_flow.get_credentials_interactively"
            ) as mock_get_creds,
            patch("monzoh.cli.auth_flow.save_credentials_to_env"),
            patch("monzoh.cli.auth_flow.start_callback_server") as mock_start_server,
            patch("monzoh.cli.auth_flow.MonzoOAuth") as mock_oauth_class,
            patch("monzoh.cli.auth_flow.secrets.token_urlsafe") as mock_token,
            patch("monzoh.cli.auth_flow.webbrowser.open"),
            patch("monzoh.cli.auth_flow.MonzoClient") as mock_client_class,
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

            with patch("monzoh.cli.token_cache.save_token_to_cache"):
                result = authenticate()

            assert result == "new_access_token"

    @patch("monzoh.cli.auth_flow.load_token_from_cache")
    def test_authenticate_keyboard_interrupt(self, mock_load_cache: Mock) -> None:
        """Test authentication cancelled by keyboard interrupt.

        Args:
            mock_load_cache: Mock load cache fixture.
        """
        mock_load_cache.side_effect = KeyboardInterrupt()

        result = authenticate()
        assert result is None

    @patch("monzoh.cli.auth_flow.load_token_from_cache")
    def test_authenticate_timeout(self, mock_load_cache: Mock) -> None:
        """Test authentication timeout.

        Args:
            mock_load_cache: Mock load cache fixture.
        """
        mock_load_cache.return_value = None

        with (
            patch("monzoh.cli.auth_flow.Console") as mock_console_class,
            patch("monzoh.cli.auth_flow.load_env_credentials") as mock_load_env,
            patch(
                "monzoh.cli.auth_flow.get_credentials_interactively"
            ) as mock_get_creds,
            patch("monzoh.cli.auth_flow.save_credentials_to_env"),
            patch("monzoh.cli.auth_flow.start_callback_server") as mock_start_server,
            patch("monzoh.cli.auth_flow.MonzoOAuth") as mock_oauth_class,
            patch("monzoh.cli.auth_flow.secrets.token_urlsafe"),
            patch("monzoh.cli.auth_flow.webbrowser.open"),
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


def test_main_success() -> None:
    """Test main function with successful authentication."""
    with (
        patch("monzoh.cli.authenticate") as mock_authenticate,
        patch("builtins.print") as mock_print,
    ):
        mock_authenticate.return_value = "test_token"

        main()
        mock_print.assert_called()


def test_main_failure() -> None:
    """Test main function with failed authentication."""
    import pytest

    with (
        patch("monzoh.cli.authenticate") as mock_authenticate,
        patch("builtins.print"),
        pytest.raises(SystemExit),
    ):
        mock_authenticate.return_value = None

        main()


def test_main_keyboard_interrupt() -> None:
    """Test main function with keyboard interrupt."""
    import pytest

    with (
        patch("monzoh.cli.authenticate") as mock_authenticate,
        patch("builtins.print"),
        pytest.raises(SystemExit),
    ):
        mock_authenticate.side_effect = KeyboardInterrupt()

        main()
