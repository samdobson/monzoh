"""Tests for async base client."""

import pytest

from monzoh.core.async_base import AsyncMockResponse


class TestAsyncMockResponse:
    """Test MockAsyncResponse class."""

    def test_async_mock_response_json(self) -> None:
        """Test AsyncMockResponse json method."""
        data = {"test": "data"}
        response = AsyncMockResponse(data, 200)

        assert response.json() == data

    def test_async_mock_response_raise_for_status_success(self) -> None:
        """Test AsyncMockResponse raise_for_status with success status."""
        response = AsyncMockResponse({}, 200)

        # Should not raise an exception
        response.raise_for_status()

    def test_async_mock_response_raise_for_status_error(self) -> None:
        """Test AsyncMockResponse raise_for_status with error status."""
        response = AsyncMockResponse({}, 400)

        with pytest.raises(Exception, match="HTTP 400 error"):
            response.raise_for_status()

    def test_async_mock_response_raise_for_status_server_error(self) -> None:
        """Test AsyncMockResponse raise_for_status with server error."""
        response = AsyncMockResponse({}, 500)

        with pytest.raises(Exception, match="HTTP 500 error"):
            response.raise_for_status()
