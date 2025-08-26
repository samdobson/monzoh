"""Tests for CLI token caching functionality."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from rich.console import Console

from monzoh.cli.token_cache import (
    clear_token_cache,
    get_token_cache_path,
    load_token_from_cache,
    save_token_to_cache,
    try_refresh_token,
)
from monzoh.models import OAuthToken


class TestTokenCache:
    """Tests for token caching functionality."""

    def test_get_token_cache_path_basic(self) -> None:
        """Test getting cache path."""
        with patch("platform.system", return_value="Darwin"):
            path = get_token_cache_path()
            assert str(path).endswith("monzoh/tokens.json")

    def test_save_token_to_cache(self) -> None:
        """Test saving token to cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            token = OAuthToken(
                access_token="test_access",
                token_type="Bearer",
                expires_in=3600,
                refresh_token="test_refresh",
                user_id="user123",
                client_id="client123",
            )
            console = Console()

            with (
                patch(
                    "monzoh.cli.token_cache.get_token_cache_path",
                    return_value=cache_path,
                ),
                patch.object(console, "print"),
            ):
                save_token_to_cache(token, console)

            assert cache_path.exists()

            with open(cache_path) as f:
                data = json.load(f)

            assert data["access_token"] == "test_access"
            assert data["refresh_token"] == "test_refresh"
            assert data["user_id"] == "user123"
            assert "expires_at" in data

    def test_save_token_to_cache_error(self) -> None:
        """Test error handling when saving token to cache."""
        token = OAuthToken(
            access_token="test_access",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="test_refresh",
            user_id="user123",
            client_id="client123",
        )
        console = Console()

        with (
            patch(
                "monzoh.cli.token_cache.get_token_cache_path",
                side_effect=Exception("Permission denied"),
            ),
            patch.object(console, "print") as mock_print,
        ):
            save_token_to_cache(token, console)
            # Should print warning but not raise
            mock_print.assert_called()

    def test_load_token_from_cache_valid(self) -> None:
        """Test loading valid token from cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            # Create cache with future expiry
            expires_at = datetime.now() + timedelta(hours=1)
            cache_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_at": expires_at.isoformat(),
                "user_id": "user123",
                "client_id": "client123",
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                result = load_token_from_cache()

            assert result is not None
            assert result["access_token"] == "test_access"

    def test_load_token_from_cache_expired(self) -> None:
        """Test loading expired token from cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            # Create cache with past expiry
            expires_at = datetime.now() - timedelta(hours=1)
            cache_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_at": expires_at.isoformat(),
                "user_id": "user123",
                "client_id": "client123",
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                result = load_token_from_cache()

            assert result is None

    def test_load_token_from_cache_expired_with_include_expired(self) -> None:
        """Test loading expired token from cache with include_expired=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"

            # Create cache with past expiry
            expires_at = datetime.now() - timedelta(hours=1)
            cache_data = {
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_at": expires_at.isoformat(),
                "user_id": "user123",
                "client_id": "client123",
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                result = load_token_from_cache(include_expired=True)

            assert result is not None
            assert result["access_token"] == "test_access"
            assert result["refresh_token"] == "test_refresh"

    def test_load_token_from_cache_missing(self) -> None:
        """Test loading token when cache file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "nonexistent.json"

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                result = load_token_from_cache()

            assert result is None

    def test_clear_token_cache(self) -> None:
        """Test clearing token cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "tokens.json"
            cache_path.write_text('{"test": "data"}')

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                clear_token_cache()

            assert not cache_path.exists()

    def test_clear_token_cache_missing_file(self) -> None:
        """Test clearing cache when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "nonexistent.json"

            with patch(
                "monzoh.cli.token_cache.get_token_cache_path", return_value=cache_path
            ):
                # Should not raise exception
                clear_token_cache()


class TestTryRefreshToken:
    """Tests for token refresh functionality."""

    def test_refresh_token_success(self) -> None:
        """Test successful token refresh."""
        cached_token = {"refresh_token": "test_refresh"}
        oauth_mock = Mock()
        console = Console()

        new_token = OAuthToken(
            access_token="new_access",
            token_type="Bearer",
            expires_in=3600,
            refresh_token="new_refresh",
            user_id="user123",
            client_id="client123",
        )
        oauth_mock.refresh_token.return_value = new_token
        oauth_mock.__enter__ = Mock(return_value=oauth_mock)
        oauth_mock.__exit__ = Mock(return_value=None)

        with (
            patch("monzoh.cli.token_cache.save_token_to_cache"),
            patch.object(console, "print"),
        ):
            result = try_refresh_token(cached_token, oauth_mock, console)

        assert result == "new_access"
        oauth_mock.refresh_token.assert_called_once_with("test_refresh")

    def test_refresh_token_failure(self) -> None:
        """Test failed token refresh."""
        cached_token = {"refresh_token": "test_refresh"}
        oauth_mock = Mock()
        console = Console()

        oauth_mock.refresh_token.side_effect = Exception("Refresh failed")
        oauth_mock.__enter__ = Mock(return_value=oauth_mock)
        oauth_mock.__exit__ = Mock(return_value=None)

        with (
            patch("monzoh.cli.token_cache.clear_token_cache") as mock_clear,
            patch.object(console, "print"),
        ):
            result = try_refresh_token(cached_token, oauth_mock, console)

        assert result is None
        mock_clear.assert_called_once()

    def test_refresh_token_no_refresh_token(self) -> None:
        """Test refresh when no refresh token available."""
        cached_token: dict[str, Any] = {}
        oauth_mock = Mock()
        console = Console()

        result = try_refresh_token(cached_token, oauth_mock, console)

        assert result is None
        oauth_mock.refresh_token.assert_not_called()
