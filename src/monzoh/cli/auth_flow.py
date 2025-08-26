"""Main authentication flow orchestration."""

import secrets
import urllib.parse
import webbrowser

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..auth import MonzoOAuth
from ..main import MonzoClient
from .credentials import (
    get_credentials_interactively,
    load_env_credentials,
    save_credentials_to_env,
)
from .oauth_server import start_callback_server
from .token_cache import (
    clear_token_cache,
    load_token_from_cache,
    save_token_to_cache,
    try_refresh_token,
)


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
        # Check for cached token first (including expired ones)
        cached_token = load_token_from_cache(include_expired=True)
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
                console.print("❌ Error during authentication: Token is invalid")

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
