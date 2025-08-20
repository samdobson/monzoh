"""OAuth2 authentication client for Monzo API."""

from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .exceptions import MonzoAuthenticationError, create_error_from_response
from .models import OAuthToken


class MonzoOAuth:
    """OAuth2 client for Monzo API authentication."""

    BASE_URL = "https://api.monzo.com"
    AUTH_URL = "https://auth.monzo.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        """Initialize OAuth client.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            http_client: Optional httpx client to use
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._http_client = http_client
        self._own_client = http_client is None

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client()
        return self._http_client

    def __enter__(self) -> "MonzoOAuth":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._own_client and self._http_client:
            self._http_client.close()

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL for OAuth flow.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
        }
        if state:
            params["state"] = state

        return f"{self.AUTH_URL}/?{urlencode(params)}"

    def exchange_code_for_token(self, authorization_code: str) -> OAuthToken:
        """Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            OAuth token response

        Raises:
            MonzoAuthenticationError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": authorization_code,
        }

        try:
            response = self.http_client.post(f"{self.BASE_URL}/oauth2/token", data=data)

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                raise create_error_from_response(
                    response.status_code,
                    f"Token exchange failed: {response.text}",
                    error_data,
                )

            return OAuthToken(**response.json())

        except httpx.RequestError as e:
            raise MonzoAuthenticationError(f"Network error during token exchange: {e}")

    def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh an access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New OAuth token response

        Raises:
            MonzoAuthenticationError: If token refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        try:
            response = self.http_client.post(f"{self.BASE_URL}/oauth2/token", data=data)

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                raise create_error_from_response(
                    response.status_code,
                    f"Token refresh failed: {response.text}",
                    error_data,
                )

            return OAuthToken(**response.json())

        except httpx.RequestError as e:
            raise MonzoAuthenticationError(f"Network error during token refresh: {e}")

    def logout(self, access_token: str) -> None:
        """Invalidate an access token.

        Args:
            access_token: Access token to invalidate

        Raises:
            MonzoAuthenticationError: If logout fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self.http_client.post(
                f"{self.BASE_URL}/oauth2/logout", headers=headers
            )

            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                raise create_error_from_response(
                    response.status_code, f"Logout failed: {response.text}", error_data
                )

        except httpx.RequestError as e:
            raise MonzoAuthenticationError(f"Network error during logout: {e}")
