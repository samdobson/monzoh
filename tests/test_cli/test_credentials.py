"""Tests for CLI credentials functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from rich.console import Console

from monzoh.cli.credentials import (
    get_credentials_interactively,
    load_env_credentials,
    save_credentials_to_env,
)


class TestLoadEnvCredentials:
    """Tests for loading environment credentials."""

    def test_load_from_env_variables(self) -> None:
        """Test loading credentials from environment variables."""
        with patch.dict(
            os.environ,
            {
                "MONZO_CLIENT_ID": "test_id",
                "MONZO_CLIENT_SECRET": "test_secret",
                "MONZO_REDIRECT_URI": "http://localhost:3000/callback",
            },
        ):
            creds = load_env_credentials()
            assert creds["client_id"] == "test_id"
            assert creds["client_secret"] == "test_secret"
            assert creds["redirect_uri"] == "http://localhost:3000/callback"

    def test_load_with_defaults(self) -> None:
        """Test loading with default redirect URI."""
        creds = load_env_credentials()
        # At minimum should have redirect_uri default
        assert "redirect_uri" in creds

    @patch("monzoh.cli.credentials.load_dotenv")
    @patch("pathlib.Path.exists")
    def test_load_with_dotenv_file(
        self, mock_exists: Mock, mock_load_dotenv: Mock
    ) -> None:
        """Test loading with .env file."""
        mock_exists.return_value = True

        with patch.dict(os.environ, {"MONZO_CLIENT_ID": "from_env"}):
            creds = load_env_credentials()
            mock_load_dotenv.assert_called_once()
            assert creds["client_id"] == "from_env"


class TestGetCredentialsInteractively:
    """Tests for interactive credential gathering."""

    def test_with_existing_credentials(self) -> None:
        """Test when credentials already exist."""
        console = Console()
        existing_creds: dict[str, str | None] = {
            "client_id": "existing_id",
            "client_secret": "existing_secret",
            "redirect_uri": "http://localhost:8080/callback",
        }

        with patch.object(console, "print"):
            creds = get_credentials_interactively(console, existing_creds)

        assert creds["client_id"] == "existing_id"
        assert creds["client_secret"] == "existing_secret"
        assert creds["redirect_uri"] == "http://localhost:8080/callback"

    @patch("monzoh.cli.credentials.Prompt.ask")
    def test_with_missing_credentials(self, mock_prompt: Mock) -> None:
        """Test when credentials need to be prompted."""
        console = Console()
        existing_creds: dict[str, str | None] = {
            "client_id": None,
            "client_secret": None,
            "redirect_uri": None,
        }

        mock_prompt.side_effect = ["new_id", "new_secret"]

        with patch.object(console, "print"):
            creds = get_credentials_interactively(console, existing_creds)

        assert creds["client_id"] == "new_id"
        assert creds["client_secret"] == "new_secret"
        assert creds["redirect_uri"] == "http://localhost:8080/callback"


class TestSaveCredentialsToEnv:
    """Tests for saving credentials to .env file."""

    def test_save_to_new_file(self) -> None:
        """Test saving credentials to new .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            console = Console()
            creds = {
                "client_id": "test_id",
                "client_secret": "test_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            with (
                patch("monzoh.cli.credentials.Confirm.ask", return_value=True),
                patch.object(console, "print"),
            ):
                save_credentials_to_env(creds, console)

            env_path = Path(".env")
            assert env_path.exists()

            content = env_path.read_text()
            assert "MONZO_CLIENT_ID=test_id" in content
            assert "MONZO_CLIENT_SECRET=test_secret" in content
            assert "MONZO_REDIRECT_URI=http://localhost:8080/callback" in content

    def test_save_to_existing_file(self) -> None:
        """Test saving credentials to existing .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            env_path = Path(".env")
            env_path.write_text("EXISTING_VAR=value\nMONZO_CLIENT_ID=old_id\n")

            console = Console()
            creds = {
                "client_id": "new_id",
                "client_secret": "new_secret",
                "redirect_uri": "http://localhost:8080/callback",
            }

            with (
                patch("monzoh.cli.credentials.Confirm.ask", return_value=True),
                patch.object(console, "print"),
            ):
                save_credentials_to_env(creds, console)

            content = env_path.read_text()
            assert "EXISTING_VAR=value" in content
            assert "MONZO_CLIENT_ID=new_id" in content
            assert "old_id" not in content

    def test_save_function_exists(self) -> None:
        """Test that save function exists."""
        assert save_credentials_to_env is not None
