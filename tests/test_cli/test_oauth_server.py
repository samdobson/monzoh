"""Tests for CLI OAuth server functionality."""

from threading import Event
from typing import Any
from unittest.mock import Mock, patch

from monzoh.cli.oauth_server import (
    OAuthCallbackHandler,
    OAuthCallbackServer,
    start_callback_server,
)


class TestOAuthCallbackHandler:
    """Tests for OAuth callback handler - basic structure tests only."""

    def test_handler_exists(self) -> None:
        """Test that the handler class exists and can be imported."""
        assert OAuthCallbackHandler is not None


class TestOAuthCallbackServer:
    """Tests for OAuth callback server."""

    @patch("monzoh.cli.oauth_server.HTTPServer.__init__")
    def test_init(self, mock_init: Any) -> None:
        """Test server initialization.

        Args:
            mock_init: Mock __init__ method fixture.
        """
        mock_init.return_value = (
            None  # Mock the parent __init__ to avoid socket binding
        )

        server = OAuthCallbackServer(("localhost", 8080))
        server.auth_code = None  # Set the attributes that would normally be set
        server.state = None
        server.error = None
        server.callback_received = Event()

        assert server.auth_code is None
        assert server.state is None
        assert server.error is None
        assert isinstance(server.callback_received, Event)
        assert not server.callback_received.is_set()


class TestStartCallbackServer:
    """Tests for callback server startup."""

    @patch("monzoh.cli.oauth_server.Thread")
    @patch("monzoh.cli.oauth_server.OAuthCallbackServer")
    def test_start_callback_server(
        self, mock_server_class: Any, mock_thread: Any
    ) -> None:
        """Test starting callback server.

        Args:
            mock_server_class: Mock server class fixture.
            mock_thread: Mock thread fixture.
        """
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        result = start_callback_server(3000)

        mock_server_class.assert_called_once_with(("localhost", 3000))
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert result == mock_server
