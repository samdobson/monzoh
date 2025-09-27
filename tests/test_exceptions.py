"""Tests for exceptions."""

from typing import TYPE_CHECKING

from monzoh.exceptions import (
    MonzoAuthenticationError,
    MonzoBadRequestError,
    MonzoError,
    MonzoNetworkError,
    MonzoNotFoundError,
    MonzoRateLimitError,
    MonzoServerError,
    create_error_from_response,
)

if TYPE_CHECKING:
    from monzoh.types import JSONObject


class TestExceptions:
    """Test exception classes."""

    def test_monzo_error(self) -> None:
        """Test base MonzoError."""
        error = MonzoError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_monzo_error_with_response_data(self) -> None:
        """Test MonzoError with response data."""
        response_data: JSONObject = {
            "message": "Custom API message",
            "code": "invalid_request",
        }
        error = MonzoError("API Error", status_code=400, response_data=response_data)

        assert error.original_message == "API Error"
        assert error.status_code == 400
        assert error.response_data == response_data
        assert str(error) == "Custom API message"

    def test_monzo_error_with_simple_data(self) -> None:
        """Test MonzoError with simple response data."""
        response_data: JSONObject = {"code": "bad_request"}
        error = MonzoError("API Error", response_data=response_data)

        assert str(error) == "API error: bad_request"

    def test_monzo_authentication_error(self) -> None:
        """Test MonzoAuthenticationError."""
        error = MonzoAuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, MonzoError)

    def test_monzo_bad_request_error(self) -> None:
        """Test MonzoBadRequestError."""
        error = MonzoBadRequestError("Bad request")
        assert str(error) == "Bad request"
        assert isinstance(error, MonzoError)

    def test_monzo_not_found_error(self) -> None:
        """Test MonzoNotFoundError."""
        error = MonzoNotFoundError("Not found")
        assert str(error) == "Not found"
        assert isinstance(error, MonzoError)

    def test_monzo_rate_limit_error(self) -> None:
        """Test MonzoRateLimitError."""
        error = MonzoRateLimitError("Rate limited")

        assert str(error) == (
            "Rate limit exceeded: You're making requests too quickly. "
            "Please wait a moment and try again."
        )
        assert isinstance(error, MonzoError)

    def test_monzo_server_error(self) -> None:
        """Test MonzoServerError."""
        error = MonzoServerError("Server error")
        assert str(error) == "Server error"
        assert isinstance(error, MonzoError)

    def test_monzo_network_error(self) -> None:
        """Test MonzoNetworkError."""
        error = MonzoNetworkError("Network error")
        assert str(error) == "Network error: Network error"
        assert isinstance(error, MonzoError)

    def test_create_error_from_response_401(self) -> None:
        """Test create_error_from_response for 401."""
        error = create_error_from_response(401, "Unauthorized", {})
        assert isinstance(error, MonzoAuthenticationError)
        assert str(error) == (
            "Authentication failed: Your access token is invalid or expired. "
            "Please run 'monzoh-auth' to authenticate again."
        )

    def test_create_error_from_response_400(self) -> None:
        """Test create_error_from_response for 400."""
        error = create_error_from_response(400, "Bad request", {})
        assert isinstance(error, MonzoBadRequestError)
        assert str(error) == "Bad request"

    def test_create_error_from_response_403(self) -> None:
        """Test create_error_from_response for 403."""
        error = create_error_from_response(403, "Forbidden", {})
        assert isinstance(error, MonzoAuthenticationError)
        assert "forbidden" in str(error).lower() or "permission" in str(error).lower()

    def test_create_error_from_response_404(self) -> None:
        """Test create_error_from_response for 404."""
        error = create_error_from_response(404, "Not found", {})
        assert isinstance(error, MonzoNotFoundError)
        assert str(error) == "Not found"

    def test_create_error_from_response_429(self) -> None:
        """Test create_error_from_response for 429."""
        error = create_error_from_response(429, "Rate limited", {})
        assert isinstance(error, MonzoRateLimitError)
        assert str(error) == (
            "Rate limit exceeded: You're making requests too quickly. "
            "Please wait a moment and try again."
        )

    def test_create_error_from_response_500(self) -> None:
        """Test create_error_from_response for 500."""
        error = create_error_from_response(500, "Server error", {})
        assert isinstance(error, MonzoServerError)
        assert str(error) == "Server error"

    def test_create_error_from_response_other(self) -> None:
        """Test create_error_from_response for other status codes."""
        error = create_error_from_response(418, "I'm a teapot", {})
        assert isinstance(error, MonzoError)
        assert str(error) == "I'm a teapot"

    def test_monzo_error_json_parsing_success(self) -> None:
        """Test MonzoError JSON parsing with valid JSON message."""
        json_message = (
            'API request failed: {"message": "Invalid request", "code": "bad_request"}'
        )
        error = MonzoError(json_message)

        assert str(error) == "Invalid request"
        assert error.original_message == json_message

    def test_monzo_error_json_parsing_failure(self) -> None:
        """Test MonzoError JSON parsing with invalid JSON."""
        invalid_json = "API request failed: Invalid JSON {not valid}"
        error = MonzoError(invalid_json)

        assert str(error) == invalid_json
        assert error.original_message == invalid_json

    def test_monzo_error_json_parsing_no_message_key(self) -> None:
        """Test MonzoError JSON parsing when JSON doesn't contain message key."""
        json_without_message = (
            'API request failed: {"code": "bad_request", "details": "Some details"}'
        )
        error = MonzoError(json_without_message)

        assert str(error) == json_without_message
        assert error.original_message == json_without_message

    def test_monzo_error_json_parsing_non_dict(self) -> None:
        """Test MonzoError JSON parsing when JSON is not a dictionary."""
        json_array = 'API request failed: ["error1", "error2"]'
        error = MonzoError(json_array)

        assert str(error) == json_array
        assert error.original_message == json_array
