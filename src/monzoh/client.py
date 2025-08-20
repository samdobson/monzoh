"""Base API client for Monzo API."""

import json
from typing import Any, Optional, Union

import httpx

from .exceptions import MonzoNetworkError, create_error_from_response
from .mock_data import get_mock_response
from .models import WhoAmI


class MockResponse:
    """Mock HTTP response for testing purposes."""

    def __init__(self, json_data: dict[str, Any], status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
        # Add httpx.Response-like attributes
        self.headers: dict[str, str] = {}
        self.cookies: dict[str, str] = {}
        self.url = ""
        self.request = None

    def json(self) -> dict[str, Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        """Mock implementation of raise_for_status."""
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code} error")


class BaseSyncClient:
    """Synchronous base HTTP client for Monzo API operations."""

    BASE_URL = "https://api.monzo.com"

    def __init__(
        self,
        access_token: str,
        http_client: Optional[httpx.Client] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize base sync client.

        Args:
            access_token: OAuth access token
            http_client: Optional httpx sync client to use
            timeout: Request timeout in seconds
        """
        self.access_token = access_token
        self._http_client = http_client
        self._own_client = http_client is None
        self._timeout = timeout

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self._timeout, headers={"User-Agent": "monzoh-python-client"}
            )
        return self._http_client

    @property
    def auth_headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    @property
    def is_mock_mode(self) -> bool:
        """Check if client is in mock mode (using 'test' as access token)."""
        return self.access_token == "test"

    def __enter__(self) -> "BaseSyncClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._own_client and self._http_client:
            self._http_client.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: URL parameters
            data: Form data
            json_data: JSON data
            files: File uploads
            headers: Additional headers

        Returns:
            HTTP response

        Raises:
            MonzoError: If request fails
        """
        # Return mock data if using test token
        if self.is_mock_mode:
            mock_data = get_mock_response(
                endpoint, method, params=params, data=data, json_data=json_data
            )
            return MockResponse(mock_data)

        url = f"{self.BASE_URL}{endpoint}"

        # Combine headers
        all_headers = self.auth_headers.copy()
        if headers:
            all_headers.update(headers)

        try:
            response = self.http_client.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                files=files,
                headers=all_headers,
            )

            # Handle non-success status codes
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass

                raise create_error_from_response(
                    response.status_code,
                    f"API request failed: {response.text}",
                    error_data,
                )

            return response

        except httpx.RequestError as e:
            raise MonzoNetworkError(f"Network error: {e}")

    def _get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make GET request."""
        return self._request("GET", endpoint, params=params, headers=headers)

    def _post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make POST request."""
        return self._request(
            "POST",
            endpoint,
            data=data,
            json_data=json_data,
            files=files,
            headers=headers,
        )

    def _put(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make PUT request."""
        return self._request(
            "PUT", endpoint, data=data, json_data=json_data, headers=headers
        )

    def _patch(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make PATCH request."""
        return self._request("PATCH", endpoint, data=data, headers=headers)

    def _delete(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> Union[httpx.Response, MockResponse]:
        """Make DELETE request."""
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def whoami(self) -> WhoAmI:
        """Get information about the current access token.

        Returns:
            Authentication information
        """
        response = self._get("/ping/whoami")
        return WhoAmI(**response.json())

    def _prepare_expand_params(
        self, expand: Optional[list] = None
    ) -> Optional[dict[str, Any]]:
        """Prepare expand parameters for requests.

        Args:
            expand: List of fields to expand

        Returns:
            Formatted expand parameters
        """
        if not expand:
            return None

        # Format expand parameters as expand[]=field1&expand[]=field2
        return {"expand[]": field for field in expand}

    def _prepare_pagination_params(
        self,
        limit: Optional[int] = None,
        since: Optional[Union[str, Any]] = None,
        before: Optional[Union[str, Any]] = None,
    ) -> dict[str, Any]:
        """Prepare pagination parameters.

        Args:
            limit: Maximum number of results
            since: Start time or object ID
            before: End time

        Returns:
            Formatted pagination parameters
        """
        params = {}
        if limit is not None:
            params["limit"] = str(limit)
        if since is not None:
            params["since"] = str(since)
        if before is not None:
            params["before"] = str(before)
        return params
