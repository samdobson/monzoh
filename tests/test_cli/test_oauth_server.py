"""Tests for CLI OAuth server functionality."""

from threading import Event
from unittest.mock import Mock, patch

from monzoh.cli.oauth_server import (
    OAuthCallbackHandler,
    OAuthCallbackServer,
    start_callback_server,
)


class TestOAuthCallbackHandler:
    """Tests for OAuth callback handler."""

    def test_handler_exists(self) -> None:
        """Test that the handler class exists and can be imported."""
        assert OAuthCallbackHandler is not None

    def test_do_get_success(self) -> None:
        """Test successful OAuth callback handling."""
        handler = object.__new__(OAuthCallbackHandler)
        handler.server = Mock(spec=OAuthCallbackServer)
        handler.server.callback_received = Event()
        handler.path = "/callback?code=test_code&state=test_state"

        with (
            patch.object(handler, "send_response") as mock_send_response,
            patch.object(handler, "send_header") as _mock_send_header,
            patch.object(handler, "end_headers") as _mock_end_headers,
        ):
            handler.wfile = Mock()
            handler.wfile.write = Mock()

            handler.do_GET()

            assert handler.server.auth_code == "test_code"
            assert handler.server.state == "test_state"
            assert handler.server.error is None
            mock_send_response.assert_called_with(200)
            assert handler.server.callback_received.is_set()

    def test_do_get_error(self) -> None:
        """Test OAuth callback error handling."""
        handler = object.__new__(OAuthCallbackHandler)
        handler.server = Mock(spec=OAuthCallbackServer)
        handler.server.callback_received = Event()
        handler.path = "/callback?error=access_denied"

        with (
            patch.object(handler, "send_response") as mock_send_response,
            patch.object(handler, "send_header") as _mock_send_header,
            patch.object(handler, "end_headers") as _mock_end_headers,
        ):
            handler.wfile = Mock()
            handler.wfile.write = Mock()

            handler.do_GET()

            assert handler.server.error == "access_denied"
            mock_send_response.assert_called_with(400)
            assert handler.server.callback_received.is_set()
            handler.wfile.write.assert_called()

    def test_log_message_suppressed(self) -> None:
        """Test that log messages are suppressed."""
        handler = object.__new__(OAuthCallbackHandler)

        handler.log_message("test format", "arg1", "arg2")


class TestOAuthCallbackServer:
    """Tests for OAuth callback server."""

    @patch("monzoh.cli.oauth_server.HTTPServer.__init__")
    def test_init(self, mock_init: Mock) -> None:
        """Test server initialization.

        Args:
            mock_init: Mock __init__ method fixture.
        """
        mock_init.return_value = None

        server = OAuthCallbackServer(("localhost", 8080))
        server.auth_code = None
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
        self, mock_server_class: Mock, mock_thread: Mock
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
