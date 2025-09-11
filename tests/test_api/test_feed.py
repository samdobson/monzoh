"""Tests for feed API."""

from typing import Any

from monzoh.api.feed import FeedAPI
from monzoh.models.feed import FeedItemParams


class TestFeedAPI:
    """Test FeedAPI."""

    def test_init(self, monzo_client: Any) -> None:
        """Test client initialization.

        Args:
            monzo_client: Monzo client fixture.
        """
        api = FeedAPI(monzo_client._base_client)
        assert api.client is monzo_client._base_client

    def test_create_item_minimal(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create item with minimal parameters.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        params = FeedItemParams(
            title="Test Title", image_url="https://example.com/image.jpg"
        )
        api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        monzo_client._base_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "type": "basic",
                "params[title]": "Test Title",
                "params[image_url]": "https://example.com/image.jpg",
            },
        )

    def test_create_item_full(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create item with all parameters.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        params = FeedItemParams(
            title="Test Title",
            image_url="https://example.com/image.jpg",
            body="Test body text",
            url="https://example.com/redirect",
            background_color="#FF0000",
            title_color="#000000",
            body_color="#333333",
        )
        api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        monzo_client._base_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "type": "basic",
                "url": "https://example.com/redirect",
                "params[title]": "Test Title",
                "params[image_url]": "https://example.com/image.jpg",
                "params[body]": "Test body text",
                "params[background_color]": "#FF0000",
                "params[title_color]": "#000000",
                "params[body_color]": "#333333",
            },
        )

    def test_create_item_partial(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
    ) -> None:
        """Test create item with some optional parameters.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response(json_data={})
        monzo_client._base_client._post.return_value = mock_response

        api = FeedAPI(monzo_client._base_client)
        params = FeedItemParams(
            title="Test Title",
            image_url="https://example.com/image.jpg",
            url="https://example.com/redirect",
            title_color="#000000",
        )
        api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        monzo_client._base_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "type": "basic",
                "url": "https://example.com/redirect",
                "params[title]": "Test Title",
                "params[image_url]": "https://example.com/image.jpg",
                "params[title_color]": "#000000",
            },
        )
