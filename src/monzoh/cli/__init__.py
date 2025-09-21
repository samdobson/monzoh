"""CLI package for Monzo OAuth authentication."""

import sys

from .auth_flow import authenticate
from .credentials import (
    get_credentials_interactively,
    load_env_credentials,
    save_credentials_to_env,
)
from .oauth_server import (
    OAuthCallbackHandler,
    OAuthCallbackServer,
    start_callback_server,
)
from .token_cache import (
    clear_token_cache,
    get_token_cache_path,
    load_token_from_cache,
    save_token_to_cache,
    try_refresh_token,
)


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
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)


__all__ = [
    "OAuthCallbackHandler",
    "OAuthCallbackServer",
    "authenticate",
    "clear_token_cache",
    "get_credentials_interactively",
    "get_token_cache_path",
    "load_env_credentials",
    "load_token_from_cache",
    "main",
    "save_credentials_to_env",
    "save_token_to_cache",
    "start_callback_server",
    "try_refresh_token",
]
