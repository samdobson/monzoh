"""Base API client for Monzo API."""

from __future__ import annotations

import contextlib
import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import types
    from datetime import datetime

import httpx
from httpx import QueryParams
from typing_extensions import Self, Unpack

from monzoh.exceptions import (
    MonzoAuthenticationError,
    MonzoError,
    MonzoNetworkError,
    create_error_from_response,
)
from monzoh.models import WhoAmI

from .mock_data import get_mock_response

if TYPE_CHECKING:
    from monzoh.types import JSONObject

QueryParamsType = (
    QueryParams
    | Mapping[
        str, str | int | float | bool | None | Sequence[str | int | float | bool | None]
    ]
    | list[tuple[str, str | int | float | bool | None]]
    | tuple[tuple[str, str | int | float | bool | None], ...]
    | str
    | bytes
    | None
)


class RequestOptions(TypedDict, total=False):
    """Optional parameters for HTTP requests."""

    params: QueryParamsType
    data: Mapping[str, str | int | float | bool | list[str]] | None
    json_data: JSONObject | None
    files: Mapping[str, tuple[str, bytes, str]] | None
    headers: dict[str, str] | None


class MockResponse:
    """Mock HTTP response for testing purposes.

    Args:
        json_data: JSON data to return
        status_code: HTTP status code to simulate
    """

    def __init__(self, json_data: JSONObject, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
        self.headers: dict[str, str] = {}
        self.cookies: dict[str, str] = {}
        self.url = ""
        self.request = None

    def json(self) -> JSONObject:
        """Return JSON data from the response.

        Returns:
            JSON data as dictionary
        """
        return self._json_data

    def raise_for_status(self) -> None:
        """Mock implementation of raise_for_status.

        Raises:
            MonzoError: If status code indicates an error (>= 400)
        """
        if self.status_code >= 400:
            msg = f"HTTP {self.status_code} error"
            raise MonzoError(msg, status_code=self.status_code)


class BaseSyncClient:
    """Synchronous base HTTP client for Monzo API operations.

    Args:
        access_token: OAuth access token
        http_client: Optional httpx sync client to use
        timeout: Request timeout in seconds

    Attributes:
        BASE_URL: Base URL for Monzo API endpoints
    """

    BASE_URL = "https://api.monzo.com"

    def __init__(
        self,
        access_token: str | None,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.access_token = access_token
        self._http_client = http_client
        self._own_client = http_client is None
        self._timeout = timeout

    @property
    def http_client(self) -> httpx.Client:
        """Get or create HTTP client.

        Returns:
            The httpx client instance
        """
        if self._http_client is None:
            self._http_client = httpx.Client(
                timeout=self._timeout, headers={"User-Agent": "monzoh-python-client"}
            )
        return self._http_client

    @property
    def auth_headers(self) -> dict[str, str]:
        """Get authorization headers.

        Returns:
            Dictionary containing authorization headers

        Raises:
            MonzoAuthenticationError: If access token is not set
        """
        if not self.access_token:
            msg = "Access token is not set."
            raise MonzoAuthenticationError(msg)
        return {"Authorization": f"Bearer {self.access_token}"}

    @property
    def is_mock_mode(self) -> bool:
        """Check if client is in mock mode (using 'test' as access token).

        Returns:
            True if client is in mock mode, False otherwise
        """
        return self.access_token == "test"  # noqa: S105

    def __enter__(self) -> Self:
        """Context manager entry.

        Returns:
            The client instance
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self._own_client and self._http_client:
            self._http_client.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        **options: Unpack[RequestOptions],
    ) -> httpx.Response | MockResponse:
        """Make HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            **options: Request options including params, data, json_data, files, headers

        Returns:
            HTTP response

        Raises:
            MonzoNetworkError: If network request fails
            create_error_from_response: If API returns an error response
        """
        params: QueryParamsType | None = options.get("params")
        data: Mapping[str, str | int | float | bool | list[str]] | None = options.get(
            "data"
        )
        json_data: JSONObject | None = options.get("json_data")
        files: Mapping[str, tuple[str, bytes, str]] | None = options.get("files")
        headers: dict[str, str] | None = options.get("headers")

        if self.is_mock_mode:
            mock_data = get_mock_response(
                endpoint, method, params=params, data=data, json_data=json_data
            )
            return MockResponse(mock_data)

        url = f"{self.BASE_URL}{endpoint}"

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

            if response.status_code >= 400:
                error_data = {}
                with contextlib.suppress(ValueError, KeyError, TypeError):
                    error_data = response.json()

                raise create_error_from_response(
                    response.status_code,
                    f"API request failed: {response.text}",
                    error_data,
                )

        except httpx.RequestError as e:
            msg = f"Network error: {e}"
            raise MonzoNetworkError(msg) from e
        else:
            return response

    def _get(
        self,
        endpoint: str,
        params: QueryParamsType = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | MockResponse:
        """Make GET request.

        Args:
            endpoint: API endpoint (without base URL)
            params: URL parameters
            headers: Additional headers

        Returns:
            HTTP response or mock response
        """
        return self._request("GET", endpoint, params=params, headers=headers)

    def _post(
        self,
        endpoint: str,
        data: Mapping[str, str | int | float | bool | list[str]] | None = None,
        json_data: JSONObject | None = None,
        files: Mapping[str, tuple[str, bytes, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | MockResponse:
        """Make POST request.

        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json_data: JSON data
            files: File uploads
            headers: Additional headers

        Returns:
            HTTP response or mock response
        """
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
        data: Mapping[str, str | int | float | bool | list[str]] | None = None,
        json_data: JSONObject | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | MockResponse:
        """Make PUT request.

        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            json_data: JSON data
            headers: Additional headers

        Returns:
            HTTP response or mock response
        """
        return self._request(
            "PUT", endpoint, data=data, json_data=json_data, headers=headers
        )

    def _patch(
        self,
        endpoint: str,
        data: Mapping[str, str | int | float | bool | list[str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | MockResponse:
        """Make PATCH request.

        Args:
            endpoint: API endpoint (without base URL)
            data: Form data
            headers: Additional headers

        Returns:
            HTTP response or mock response
        """
        return self._request("PATCH", endpoint, data=data, headers=headers)

    def _delete(
        self,
        endpoint: str,
        params: QueryParamsType = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | MockResponse:
        """Make DELETE request.

        Args:
            endpoint: API endpoint (without base URL)
            params: URL parameters
            headers: Additional headers

        Returns:
            HTTP response or mock response
        """
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def whoami(self) -> WhoAmI:
        """Get information about the current access token.

        Returns:
            Authentication information
        """
        response = self._get("/ping/whoami")
        return WhoAmI(**response.json())

    def _prepare_expand_params(
        self, expand: Sequence[str] | None = None
    ) -> list[tuple[str, str | int | float | bool | None]] | None:
        """Prepare expand parameters for requests.

        Args:
            expand: List of fields to expand

        Returns:
            Formatted expand parameters
        """
        if not expand:
            return None

        return [("expand[]", field) for field in expand]

    def _prepare_pagination_params(
        self,
        limit: int | None = None,
        since: str | datetime | None = None,
        before: str | datetime | None = None,
    ) -> dict[str, str]:
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
