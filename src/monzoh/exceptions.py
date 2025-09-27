"""Custom exceptions for the Monzo API client."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from monzoh.types import JSONObject


class MonzoError(Exception):
    """Base exception for all Monzo API errors.

    Args:
        message: Error message
        status_code: HTTP status code if available
        response_data: API response data if available
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: JSONObject | None = None,
    ) -> None:
        self.original_message = message
        self.status_code = status_code
        self.response_data = response_data or {}

        friendly_message = self._create_friendly_message()
        super().__init__(friendly_message)
        self.message = friendly_message

    def _create_friendly_message(self) -> str:
        """Create a user-friendly error message.

        Returns:
            User-friendly error message
        """
        if isinstance(self.response_data, dict):
            api_message = str(self.response_data.get("message", ""))
            error_code = str(self.response_data.get("code", ""))

            if api_message:
                return api_message
            if error_code:
                return f"API error: {error_code}"

        if "API request failed:" in self.original_message:
            try:
                json_start = self.original_message.find("{")
                if json_start != -1:
                    json_part = self.original_message[json_start:]
                    data = json.loads(json_part)
                    if isinstance(data, dict) and "message" in data:
                        return str(data["message"])
            except (json.JSONDecodeError, ValueError):
                pass

        return self.original_message


class MonzoAuthenticationError(MonzoError):
    """Authentication-related errors (401, 403)."""

    def _create_friendly_message(self) -> str:
        """Create a user-friendly authentication error message.

        Returns:
            User-friendly authentication error message
        """
        base_message = super()._create_friendly_message()

        if "insufficient_permissions" in self.original_message:
            return (
                "Access forbidden: Your access token doesn't have the required "
                "permissions. You may need to approve access in the Monzo app."
            )
        if "unauthorized" in self.original_message.lower() or self.status_code == 401:
            return (
                "Authentication failed: Your access token is invalid or expired. "
                "Please run 'monzoh-auth' to authenticate again."
            )
        if self.status_code == 403:
            return (
                "Access forbidden: You don't have permission to access this resource. "
                "Your access token may lack the required scopes."
            )

        return base_message


class MonzoBadRequestError(MonzoError):
    """Bad request error (400)."""


class MonzoNotFoundError(MonzoError):
    """Resource not found error (404)."""


class MonzoMethodNotAllowedError(MonzoError):
    """Method not allowed error (405)."""


class MonzoNotAcceptableError(MonzoError):
    """Not acceptable error (406)."""


class MonzoRateLimitError(MonzoError):
    """Rate limit exceeded error (429)."""

    def _create_friendly_message(self) -> str:
        """Create a user-friendly rate limit error message.

        Returns:
            User-friendly rate limit error message
        """
        return (
            "Rate limit exceeded: You're making requests too quickly. "
            "Please wait a moment and try again."
        )


class MonzoServerError(MonzoError):
    """Internal server error (500)."""


class MonzoTimeoutError(MonzoError):
    """Gateway timeout error (504)."""


class MonzoNetworkError(MonzoError):
    """Network-related errors."""

    def _create_friendly_message(self) -> str:
        """Create a user-friendly network error message.

        Returns:
            User-friendly network error message
        """
        if "timeout" in self.original_message.lower():
            return (
                "Request timed out: The Monzo API is not responding. "
                "Please try again later."
            )
        if "connection" in self.original_message.lower():
            return (
                "Connection error: Unable to connect to the Monzo API. "
                "Please check your internet connection."
            )
        return f"Network error: {self.original_message.replace('Network error: ', '')}"


class MonzoValidationError(MonzoError):
    """Data validation errors."""


def create_error_from_response(
    status_code: int, message: str, response_data: JSONObject | None = None
) -> MonzoError:
    """Create appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code
        message: Error message
        response_data: Optional API response data

    Returns:
        Appropriate exception instance based on status code
    """
    error_map = {
        400: MonzoBadRequestError,
        401: MonzoAuthenticationError,
        403: MonzoAuthenticationError,
        404: MonzoNotFoundError,
        405: MonzoMethodNotAllowedError,
        406: MonzoNotAcceptableError,
        429: MonzoRateLimitError,
        500: MonzoServerError,
        504: MonzoTimeoutError,
    }

    error_class = error_map.get(status_code, MonzoError)
    return error_class(message, status_code, response_data)
