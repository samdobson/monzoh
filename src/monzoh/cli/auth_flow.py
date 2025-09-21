"""Main authentication flow orchestration."""

import secrets
import urllib.parse
import webbrowser

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from monzoh.auth import MonzoOAuth
from monzoh.client import MonzoClient
from monzoh.exceptions import MonzoError

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


def _try_cached_token(console: Console) -> str | None:
    """Try to use cached token, return access token if valid."""
    cached_token = load_token_from_cache(include_expired=True)
    if not cached_token:
        return None

    console.print("🔍 Found cached access token")
    console.print("🧪 Testing cached token...")

    try:
        with MonzoClient(cached_token["access_token"]) as client:
            whoami = client.whoami()
            console.print(
                f"✅ [green]Using cached token for: {whoami.user_id}[/green]"
            )
            return cached_token["access_token"]
    except Exception:
        console.print("❌ Error during authentication: Token is invalid")

        # Try to refresh the token before giving up
        if cached_token.get("refresh_token"):
            console.print("🔄 Attempting to refresh token...")
            refreshed_token = _try_refresh_cached_token(cached_token, console)
            if refreshed_token:
                return refreshed_token
        else:
            console.print("⚠️  No refresh token available")

        return None


def _try_refresh_cached_token(cached_token: dict, console: Console) -> str | None:
    """Try to refresh cached token, return access token if successful."""
    existing_creds = load_env_credentials()
    if not (existing_creds.get("client_id") and existing_creds.get("client_secret")):
        return None

    client_id = existing_creds["client_id"]
    client_secret = existing_creds["client_secret"]
    redirect_uri = existing_creds.get("redirect_uri", "http://localhost:8080/callback")

    if not client_id or not client_secret:
        msg = "Client ID and Client Secret are required"
        raise ValueError(msg) from None

    if not redirect_uri:
        redirect_uri = "http://localhost:8080/callback"

    oauth = MonzoOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    return try_refresh_token(cached_token, oauth, console)


def _perform_oauth_flow(console: Console) -> str | None:
    """Perform full OAuth flow, return access token if successful."""
    existing_creds = load_env_credentials()
    creds = get_credentials_interactively(console, existing_creds)

    if not all(existing_creds.get(k) for k in ["client_id", "client_secret"]):
        save_credentials_to_env(creds, console)

    parsed_uri = urllib.parse.urlparse(creds["redirect_uri"])
    port = parsed_uri.port or 8080

    console.print(f"\n🚀 Starting callback server on port [cyan]{port}[/cyan]...")
    server = start_callback_server(port)

    oauth = MonzoOAuth(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        redirect_uri=creds["redirect_uri"],
    )

    state = secrets.token_urlsafe(32)
    auth_url = oauth.get_authorization_url(state=state)

    console.print("\n📋 Next steps:")
    console.print(
        "1. A browser window will open with the Monzo authorization page "
        "(if not, you'll need to do it manually)"
    )
    console.print("2. Log in to your Monzo account and authorize the application")
    console.print("3. You'll be redirected back automatically")

    webbrowser.open(auth_url)
    console.print(
        f"\nIf your browser does not open automatically, use the following "
        f"link to authenticate:\n[blue]{auth_url}[/blue]"
    )

    console.print("\n⏳ Waiting for authorization... (Press Ctrl+C to cancel)")

    callback_timeout = 300
    if not server.callback_received.wait(timeout=callback_timeout):
        server.shutdown()
        console.print(f"\n⏰ [yellow]Timeout after {callback_timeout} seconds[/yellow]")
        return None

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

    with oauth:
        token = oauth.exchange_code_for_token(server.auth_code)

    console.print("🎉 [bold green]Authentication successful![/bold green]")
    console.print(f"Access Token: [green]{token.access_token[:20]}...[/green]")

    save_token_to_cache(token, console)

    console.print("\n🧪 Testing API access...")
    with MonzoClient(token.access_token) as client:
        whoami = client.whoami()
        console.print(f"✅ Connected as: [cyan]{whoami.user_id}[/cyan]")

    return token.access_token


def authenticate() -> str | None:
    """Main authentication flow."""
    console = Console()

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
        access_token = _try_cached_token(console)
        if access_token:
            return access_token

        # If we get here, cached token is either missing or refresh failed
        clear_token_cache()
        console.print("🗑️  Cleared invalid token cache")

        return _perform_oauth_flow(console)

    except KeyboardInterrupt:
        console.print("\n\n👋 [yellow]Authentication cancelled by user[/yellow]")
        return None
    except (MonzoError, OSError, ValueError) as e:
        console.print(f"\n❌ [red]Error during authentication: {e}[/red]")
        return None
