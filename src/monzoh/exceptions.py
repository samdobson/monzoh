"""Custom exceptions for the Monzo API client."""

from typing import Any, Optional


class MonzoError(Exception):
    """Base exception for all Monzo API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict[str, Any]] = None,
    ) -> None:
        self.original_message = message
        self.status_code = status_code
        self.response_data = response_data or {}

        # Create user-friendly message
        friendly_message = self._create_friendly_message()
        super().__init__(friendly_message)
        self.message = friendly_message

    def _create_friendly_message(self) -> str:
        """Create a user-friendly error message."""
        # Extract meaningful information from response data
        if isinstance(self.response_data, dict):
            # Try to get the main error message
            api_message = str(self.response_data.get("message", ""))
            error_code = str(self.response_data.get("code", ""))

            if api_message:
                return api_message
            elif error_code:
                return f"API error: {error_code}"

        # Fallback to original message, cleaned up
        if "API request failed:" in self.original_message:
            # Try to extract just the meaningful part
            try:
                import json

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
        """Create a user-friendly authentication error message."""
        # First try the parent's logic
        base_message = super()._create_friendly_message()

        # Add context-specific improvements for auth errors
        if "insufficient_permissions" in self.original_message:
            return (
                "Access forbidden: Your access token doesn't have the required "
                "permissions. You may need to approve access in the Monzo app."
            )
        elif "unauthorized" in self.original_message.lower():
            return (
                "Authentication failed: Your access token is invalid or expired. "
                "Please run 'monzoh-auth' to authenticate again."
            )
        elif self.status_code == 401:
            return (
                "Authentication failed: Your access token is invalid or expired. "
                "Please run 'monzoh-auth' to authenticate again."
            )
        elif self.status_code == 403:
            return (
                "Access forbidden: You don't have permission to access this resource. "
                "Your access token may lack the required scopes."
            )

        return base_message


class MonzoBadRequestError(MonzoError):
    """Bad request error (400)."""

    pass


class MonzoNotFoundError(MonzoError):
    """Resource not found error (404)."""

    pass


class MonzoMethodNotAllowedError(MonzoError):
    """Method not allowed error (405)."""

    pass


class MonzoNotAcceptableError(MonzoError):
    """Not acceptable error (406)."""

    pass


class MonzoRateLimitError(MonzoError):
    """Rate limit exceeded error (429)."""

    def _create_friendly_message(self) -> str:
        """Create a user-friendly rate limit error message."""
        return (
            "Rate limit exceeded: You're making requests too quickly. "
            "Please wait a moment and try again."
        )


class MonzoServerError(MonzoError):
    """Internal server error (500)."""

    pass


class MonzoTimeoutError(MonzoError):
    """Gateway timeout error (504)."""

    pass


class MonzoNetworkError(MonzoError):
    """Network-related errors."""

    def _create_friendly_message(self) -> str:
        """Create a user-friendly network error message."""
        if "timeout" in self.original_message.lower():
            return (
                "Request timed out: The Monzo API is not responding. "
                "Please try again later."
            )
        elif "connection" in self.original_message.lower():
            return (
                "Connection error: Unable to connect to the Monzo API. "
                "Please check your internet connection."
            )
        else:
            return (
                f"Network error: {self.original_message.replace('Network error: ', '')}"
            )


class MonzoValidationError(MonzoError):
    """Data validation errors."""

    pass


def create_error_from_response(
    status_code: int, message: str, response_data: Optional[dict[str, Any]] = None
) -> MonzoError:
    """Create appropriate exception based on HTTP status code."""
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
