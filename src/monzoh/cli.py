"""CLI tool for Monzo OAuth authentication."""

import json
import os
import secrets
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event, Thread
from typing import Any

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from .auth import MonzoOAuth
from .main import MonzoClient
from .models import OAuthToken


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    server: "OAuthCallbackServer"

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET request for OAuth callback."""
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)

        # Store the auth code and state
        self.server.auth_code = query_params.get("code", [None])[0]
        self.server.state = query_params.get("state", [None])[0]
        self.server.error = query_params.get("error", [None])[0]

        # Send response to browser
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

        # Signal that we got a response
        self.server.callback_received.set()

    def log_message(self, format: str, *args: Any) -> None:
        """Override to suppress request logging."""
        pass


class OAuthCallbackServer(HTTPServer):
    """HTTP server for handling OAuth callbacks."""

    def __init__(self, server_address: tuple) -> None:
        super().__init__(server_address, OAuthCallbackHandler)
        self.auth_code: str | None = None
        self.state: str | None = None
        self.error: str | None = None
        self.callback_received = Event()


def load_env_credentials() -> dict[str, str | None]:
    """Load credentials from environment variables and .env file."""
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "client_id": os.getenv("MONZO_CLIENT_ID"),
        "client_secret": os.getenv("MONZO_CLIENT_SECRET"),
        "redirect_uri": os.getenv(
            "MONZO_REDIRECT_URI", "http://localhost:8080/callback"
        ),
    }


def get_credentials_interactively(
    console: Console, existing_creds: dict[str, str | None]
) -> dict[str, str]:
    """Get missing credentials from user input."""
    creds = {}

    console.print()
    console.print(
        Panel(
            "[bold blue]Monzo OAuth Setup[/bold blue]\n\n"
            "To authenticate with the Monzo API, you'll need:\n"
            "• Client ID from your Monzo developer application\n"
            "• Client Secret from your Monzo developer application\n"
            "• Redirect URI (we'll use http://localhost:8080/callback by default)",
            title="🔐 Credentials Required",
        )
    )

    # Client ID
    if existing_creds.get("client_id"):
        client_id = existing_creds["client_id"]
        assert client_id is not None  # mypy: safe due to if condition
        console.print(f"✓ Found Client ID: [green]{client_id[:8]}...[/green]")
        creds["client_id"] = client_id
    else:
        creds["client_id"] = Prompt.ask(
            "[bold]Enter your Monzo Client ID[/bold]", console=console
        ).strip()

    # Client Secret
    if existing_creds.get("client_secret"):
        client_secret = existing_creds["client_secret"]
        assert client_secret is not None  # mypy: safe due to if condition
        console.print(f"✓ Found Client Secret: [green]{'*' * 8}[/green]")
        creds["client_secret"] = client_secret
    else:
        creds["client_secret"] = Prompt.ask(
            "[bold]Enter your Monzo Client Secret[/bold]",
            password=True,
            console=console,
        ).strip()

    # Redirect URI
    default_redirect: str = (
        existing_creds.get("redirect_uri", "http://localhost:8080/callback")
        or "http://localhost:8080/callback"
    )
    console.print(f"✓ Using Redirect URI: [green]{default_redirect}[/green]")
    creds["redirect_uri"] = default_redirect

    return creds


def start_callback_server(port: int = 8080) -> OAuthCallbackServer:
    """Start the OAuth callback server."""
    server = OAuthCallbackServer(("localhost", port))

    def run_server() -> None:
        server.serve_forever()

    # Start server in background thread
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    return server


def save_credentials_to_env(creds: dict[str, str], console: Console) -> None:
    """Offer to save credentials to .env file."""
    env_path = Path(".env")

    if not env_path.exists() or Confirm.ask(
        f"\n[yellow]Save credentials to {env_path}?[/yellow] "
        "This will help avoid entering them again.",
        console=console,
        default=True,
    ):
        env_content = []

        if env_path.exists():
            with open(env_path) as f:
                env_content = f.readlines()

        # Remove existing Monzo credentials
        env_content = [
            line
            for line in env_content
            if not line.startswith(
                ("MONZO_CLIENT_ID=", "MONZO_CLIENT_SECRET=", "MONZO_REDIRECT_URI=")
            )
        ]

        # Add new credentials
        env_content.extend(
            [
                f"MONZO_CLIENT_ID={creds['client_id']}\n",
                f"MONZO_CLIENT_SECRET={creds['client_secret']}\n",
                f"MONZO_REDIRECT_URI={creds['redirect_uri']}\n",
            ]
        )

        with open(env_path, "w") as f:
            f.writelines(env_content)

        console.print(f"✅ Credentials saved to [green]{env_path}[/green]")


def get_token_cache_path() -> Path:
    """Get path for token cache file."""
    import platform

    system = platform.system()

    if system == "Windows":
        # Use %LOCALAPPDATA% on Windows
        cache_dir = (
            Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "monzoh"
        )
    elif system == "Darwin":  # macOS
        # Use ~/Library/Caches on macOS
        cache_dir = Path.home() / "Library" / "Caches" / "monzoh"
    else:
        # Linux and other Unix-like systems: use XDG_CACHE_HOME or ~/.cache
        cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "monzoh"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "tokens.json"


def save_token_to_cache(token: OAuthToken, console: Console) -> None:
    """Save token to cache file."""
    try:
        cache_path = get_token_cache_path()

        # Calculate expiry time
        expires_at = datetime.now() + timedelta(seconds=token.expires_in)

        cache_data = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": expires_at.isoformat(),
            "user_id": token.user_id,
            "client_id": token.client_id,
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f, indent=2)

        # Set restrictive permissions (readable only by owner)
        try:
            cache_path.chmod(0o600)
        except OSError:
            # On Windows, chmod might not work as expected
            # The file is still protected by the user's directory permissions
            pass

        console.print(f"💾 Token cached to [green]{cache_path}[/green]")

    except Exception as e:
        console.print(f"⚠️  [yellow]Warning: Could not cache token: {e}[/yellow]")


def load_token_from_cache() -> dict[str, Any] | None:
    """Load token from cache file."""
    try:
        cache_path = get_token_cache_path()

        if not cache_path.exists():
            return None

        with open(cache_path) as f:
            cache_data: dict[str, Any] = json.load(f)

        # Check if token has expired
        expires_at = datetime.fromisoformat(cache_data["expires_at"])
        if datetime.now() >= expires_at - timedelta(minutes=5):  # 5 min buffer
            return None

        return cache_data

    except (OSError, ValueError, TypeError, KeyError, FileNotFoundError):
        return None


def clear_token_cache() -> None:
    """Clear the token cache."""
    try:
        cache_path = get_token_cache_path()
        if cache_path.exists():
            cache_path.unlink()
    except (OSError, ValueError, TypeError, KeyError, FileNotFoundError):
        pass


def try_refresh_token(
    cached_token: dict[str, Any], oauth: MonzoOAuth, console: Console
) -> str | None:
    """Try to refresh an expired token."""
    if not cached_token.get("refresh_token"):
        return None

    try:
        console.print("🔄 Refreshing expired access token...")

        with oauth:
            new_token = oauth.refresh_token(cached_token["refresh_token"])

        save_token_to_cache(new_token, console)
        console.print("✅ [green]Token refreshed successfully![/green]")
        return new_token.access_token

    except Exception as e:
        console.print(f"⚠️  [yellow]Token refresh failed: {e}[/yellow]")
        clear_token_cache()
        return None


def authenticate() -> str | None:
    """Main authentication flow."""
    console = Console()

    # Show welcome banner
    console.print()
    console.print(
        Panel(
            Text(
                "🏦 Monzo API Authentication Tool",
                style="bold magenta",
                justify="center",
            ),
            style="magenta",
        )
    )

    try:
        # Check for cached token first
        cached_token = load_token_from_cache()
        if cached_token:
            console.print("🔍 Found cached access token")

            # Test if token is still valid
            console.print("🧪 Testing cached token...")
            try:
                with MonzoClient(cached_token["access_token"]) as client:
                    whoami = client.whoami()
                    console.print(
                        f"✅ [green]Using cached token for: {whoami.user_id}[/green]"
                    )
                    access_token: str = cached_token["access_token"]
                    return access_token
            except (OSError, ValueError, TypeError, KeyError, FileNotFoundError):
                console.print("❌ [red]Cached token is invalid[/red]")

                # Try to refresh the token
                existing_creds = load_env_credentials()
                if existing_creds.get("client_id") and existing_creds.get(
                    "client_secret"
                ):
                    client_id = existing_creds["client_id"]
                    client_secret = existing_creds["client_secret"]
                    redirect_uri = existing_creds.get(
                        "redirect_uri", "http://localhost:8080/callback"
                    )
                    assert client_id is not None
                    assert client_secret is not None
                    assert redirect_uri is not None  # get() with default never None

                    oauth = MonzoOAuth(
                        client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                    )

                    refreshed_token = try_refresh_token(cached_token, oauth, console)
                    if refreshed_token:
                        return refreshed_token

                # Clear invalid cache
                clear_token_cache()
                console.print("🗑️  Cleared invalid token cache")

        # Load existing credentials
        existing_creds = load_env_credentials()

        # Get missing credentials interactively
        creds = get_credentials_interactively(console, existing_creds)

        # Offer to save credentials
        if not all(existing_creds.get(k) for k in ["client_id", "client_secret"]):
            save_credentials_to_env(creds, console)

        # Extract port from redirect URI
        parsed_uri = urllib.parse.urlparse(creds["redirect_uri"])
        port = parsed_uri.port or 8080

        # Start callback server
        console.print(f"\n🚀 Starting callback server on port [cyan]{port}[/cyan]...")
        server = start_callback_server(port)

        # Create OAuth client
        oauth = MonzoOAuth(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
            redirect_uri=creds["redirect_uri"],
        )

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        auth_url = oauth.get_authorization_url(state=state)

        console.print("\n📋 Next steps:")
        console.print(
            "1. A browser window will open with the Monzo authorization page "
            "(if not, you'll need to do it manually)"
        )
        console.print("2. Log in to your Monzo account and authorize the application")
        console.print("3. You'll be redirected back automatically")

        # Open browser automatically
        webbrowser.open(auth_url)
        console.print(
            f"\nIf your browser does not open automatically, use the following "
            f"link to authenticate:\n[blue]{auth_url}[/blue]"
        )

        console.print("\n⏳ Waiting for authorization... (Press Ctrl+C to cancel)")

        # Wait for callback
        callback_timeout = 300  # 5 minutes
        if server.callback_received.wait(timeout=callback_timeout):
            server.shutdown()

            if server.error:
                console.print(f"\n❌ [red]Authorization failed: {server.error}[/red]")
                return None

            if not server.auth_code:
                console.print("\n❌ [red]No authorization code received[/red]")
                return None

            if server.state != state:
                console.print(
                    "\n❌ [red]Invalid state parameter - possible CSRF attack[/red]"
                )
                return None

            console.print("\n✅ [green]Authorization code received![/green]")
            console.print("🔄 Exchanging code for access token...")

            # Exchange code for token
            with oauth:
                token = oauth.exchange_code_for_token(server.auth_code)

            console.print("🎉 [bold green]Authentication successful![/bold green]")
            console.print(f"Access Token: [green]{token.access_token[:20]}...[/green]")

            # Save token to cache
            save_token_to_cache(token, console)

            # Test the token
            console.print("\n🧪 Testing API access...")
            with MonzoClient(token.access_token) as client:
                whoami = client.whoami()
                console.print(f"✅ Connected as: [cyan]{whoami.user_id}[/cyan]")

            return token.access_token

        else:
            server.shutdown()
            console.print(
                f"\n⏰ [yellow]Timeout after {callback_timeout} seconds[/yellow]"
            )
            return None

    except KeyboardInterrupt:
        console.print("\n\n👋 [yellow]Authentication cancelled by user[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n❌ [red]Error during authentication: {e}[/red]")
        return None


def main() -> None:
    """Main CLI entry point."""
    try:
        access_token = authenticate()
        if access_token:
            print("\n💡 You can now use the MonzoClient without providing a token:")
            print("   from monzoh import MonzoClient")
            print("   client = MonzoClient()  # Will load token automatically")
        else:
            print("\n❌ Authentication failed or was cancelled")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        exit(0)


if __name__ == "__main__":
    main()
