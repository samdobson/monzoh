"""OAuth callback server for handling authentication redirects."""

import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from typing import Any


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    server: "OAuthCallbackServer"

    def do_GET(self) -> None:
        """Handle GET request for OAuth callback."""
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)

        self.server.auth_code = query_params.get("code", [None])[0]
        self.server.state = query_params.get("state", [None])[0]
        self.server.error = query_params.get("error", [None])[0]

        if self.server.auth_code:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                    <head><title>Monzo OAuth</title></head>
                    <body>
                        <h1>&#x2705; Authorization Successful!</h1>
                        <p>You can now close this window and return to the terminal.</p>
                        <script>setTimeout(() => window.close(), 3000);</script>
                    </body>
                </html>
            """
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_msg = self.server.error or "Unknown error"
            self.wfile.write(
                f"""
                <html>
                    <head><title>Monzo OAuth Error</title></head>
                    <body>
                        <h1>&#x274C; Authorization Failed</h1>
                        <p>Error: {error_msg}</p>
                        <p>Please close this window and try again.</p>
                    </body>
                </html>
            """.encode()
            )

        self.server.callback_received.set()

    def log_message(self, format: str, *args: Any) -> None:
        """Override to suppress request logging."""
        pass


class OAuthCallbackServer(HTTPServer):
    """HTTP server for handling OAuth callbacks.

    Args:
        server_address: Server address tuple (host, port)
    """

    def __init__(self, server_address: tuple) -> None:
        super().__init__(server_address, OAuthCallbackHandler)
        self.auth_code: str | None = None
        self.state: str | None = None
        self.error: str | None = None
        self.callback_received = Event()


def start_callback_server(port: int = 8080) -> OAuthCallbackServer:
    """Start the OAuth callback server.

    Args:
        port: Port number for the callback server. Defaults to 8080.

    Returns:
        OAuthCallbackServer: The running OAuth callback server instance.
    """
    server = OAuthCallbackServer(("localhost", port))

    def run_server() -> None:
        """Run the OAuth callback server indefinitely."""
        server.serve_forever()

    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    return server
