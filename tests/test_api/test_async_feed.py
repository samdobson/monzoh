"""Tests for async feed API."""

from typing import cast
from unittest.mock import Mock

import pytest

from monzoh.api.async_feed import AsyncFeedAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models.feed import FeedItemParams


class TestAsyncFeedAPI:
    """Test async feed API."""

    @pytest.fixture
    def feed_api(self, mock_async_base_client: BaseAsyncClient) -> AsyncFeedAPI:
        """Create async feed API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncFeedAPI instance.
        """
        return AsyncFeedAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_create_item_minimal(
        self,
        feed_api: AsyncFeedAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create item with minimal parameters.

        Args:
            feed_api: Async feed API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        params = FeedItemParams(
            title="Test Title", image_url="https://example.com/image.jpg"
        )
        await feed_api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "type": "basic",
                "params[title]": "Test Title",
                "params[image_url]": "https://example.com/image.jpg",
            },
        )

    @pytest.mark.asyncio
    async def test_create_item_full(
        self,
        feed_api: AsyncFeedAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create item with all parameters.

        Args:
            feed_api: Async feed API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        params = FeedItemParams(
            title="Test Title",
            image_url="https://example.com/image.jpg",
            body="Test body text",
            url="https://example.com/redirect",
            background_color="#FF0000",
            title_color="#000000",
            body_color="#333333",
        )
        await feed_api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
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

    @pytest.mark.asyncio
    async def test_create_item_partial(
        self,
        feed_api: AsyncFeedAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test create item with some optional parameters.

        Args:
            feed_api: Async feed API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        params = FeedItemParams(
            title="Test Title",
            image_url="https://example.com/image.jpg",
            url="https://example.com/redirect",
            title_color="#000000",
        )
        await feed_api.create_item("acc_00009237aqC8c5umZmrRdh", params)

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
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
