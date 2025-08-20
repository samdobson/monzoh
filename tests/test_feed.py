"""Tests for feed API."""

from typing import Any

from monzoh.feed import FeedAPI


class TestFeedAPI:
    """Test FeedAPI."""

    def test_init(self, monzo_client: Any) -> None:
        """Test client initialization."""
        api = FeedAPI(monzo_client._base_client)
        assert api.client is monzo_client._base_client

    def test_create_basic_item_minimal(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create basic item with minimal parameters."""
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        api.create_basic_item(
            "acc_00009237aqC8c5umZmrRdh", "Test Title", "https://example.com/image.jpg"
        )

    def test_create_basic_item_full(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create basic item with all parameters."""
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        api.create_basic_item(
            account_id="acc_00009237aqC8c5umZmrRdh",
            title="Test Title",
            image_url="https://example.com/image.jpg",
            body="Test body text",
            url="https://example.com/redirect",
            background_color="#FF0000",
            title_color="#000000",
            body_color="#333333",
        )

    def test_create_basic_item_partial(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create basic item with some optional parameters."""
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        api.create_basic_item(
            account_id="acc_00009237aqC8c5umZmrRdh",
            title="Test Title",
            image_url="https://example.com/image.jpg",
            url="https://example.com/redirect",
            title_color="#000000",
        )
