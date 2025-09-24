"""Credential management for Monzo OAuth."""

import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt


def load_env_credentials() -> dict[str, str | None]:
    """Load credentials from environment variables and .env file."""
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

    client_id = existing_creds.get("client_id")
    if client_id:
        console.print(f"✓ Found Client ID: [green]{client_id[:8]}...[/green]")
        creds["client_id"] = client_id
    else:
        creds["client_id"] = Prompt.ask(
            "[bold]Enter your Monzo Client ID[/bold]", console=console
        ).strip()

    client_secret = existing_creds.get("client_secret")
    if client_secret:
        console.print(f"✓ Found Client Secret: [green]{'*' * 8}[/green]")
        creds["client_secret"] = client_secret
    else:
        creds["client_secret"] = Prompt.ask(
            "[bold]Enter your Monzo Client Secret[/bold]",
            password=True,
            console=console,
        ).strip()

    default_redirect: str = (
        existing_creds.get("redirect_uri", "http://localhost:8080/callback")
        or "http://localhost:8080/callback"
    )
    console.print(f"✓ Using Redirect URI: [green]{default_redirect}[/green]")
    creds["redirect_uri"] = default_redirect

    return creds


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
            with env_path.open() as f:
                env_content = f.readlines()

        env_content = [
            line
            for line in env_content
            if not line.startswith(
                ("MONZO_CLIENT_ID=", "MONZO_CLIENT_SECRET=", "MONZO_REDIRECT_URI=")
            )
        ]

        env_content.extend(
            [
                f"MONZO_CLIENT_ID={creds['client_id']}\n",
                f"MONZO_CLIENT_SECRET={creds['client_secret']}\n",
                f"MONZO_REDIRECT_URI={creds['redirect_uri']}\n",
            ]
        )

        with env_path.open("w") as f:
            f.writelines(env_content)

        console.print(f"✅ Credentials saved to [green]{env_path}[/green]")
