"""Token caching and refresh functionality."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console

from ..auth import MonzoOAuth
from ..models import OAuthToken


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


def load_token_from_cache(include_expired: bool = False) -> dict[str, Any] | None:
    """Load token from cache file.

    Args:
        include_expired: If True, return expired tokens (useful for refresh)

    Returns:
        Cached token data if available and valid, None otherwise
    """
    try:
        cache_path = get_token_cache_path()

        if not cache_path.exists():
            return None

        with open(cache_path) as f:
            cache_data: dict[str, Any] = json.load(f)

        # Check if token has expired
        if not include_expired:
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
