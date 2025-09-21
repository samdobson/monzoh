"""Tests for async webhooks API."""

from typing import Any, cast
from unittest.mock import Mock

import pytest

from monzoh.api.async_webhooks import AsyncWebhooksAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Webhook


class TestAsyncWebhooksAPI:
    """Test async webhooks API."""

    @pytest.fixture
    def webhooks_api(self, mock_async_base_client: BaseAsyncClient) -> AsyncWebhooksAPI:
        """Create async webhooks API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncWebhooksAPI instance.
        """
        return AsyncWebhooksAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_register(
        self,
        webhooks_api: AsyncWebhooksAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test register webhook.

        Args:
            webhooks_api: Async webhooks API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        webhook_data = {
            "id": "webhook_000091yhhOmrXQaVZ1Irsv",
            "account_id": "acc_00009237aqC8c5umZmrRdh",
            "url": "http://example.com/webhook",
        }
        response_data = {"webhook": webhook_data}
        cast(
            "Mock", mock_async_base_client._post
        ).return_value.json.return_value = response_data

        result = await webhooks_api.register(
            "acc_00009237aqC8c5umZmrRdh", "http://example.com/webhook"
        )

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
            "/webhooks",
            data={
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "url": "http://example.com/webhook",
            },
        )
        assert isinstance(result, Webhook)
        assert result.id == "webhook_000091yhhOmrXQaVZ1Irsv"
        assert result.account_id == "acc_00009237aqC8c5umZmrRdh"
        assert result.url == "http://example.com/webhook"

    @pytest.mark.asyncio
    async def test_list(
        self,
        webhooks_api: AsyncWebhooksAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test list webhooks.

        Args:
            webhooks_api: Async webhooks API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        webhook_data = [
            {
                "id": "webhook_000091yhhOmrXQaVZ1Irsv",
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "url": "http://example.com/webhook",
            },
            {
                "id": "webhook_000091yhhOmrXQaVZ1Irsw",
                "account_id": "acc_00009237aqC8c5umZmrRdh",
                "url": "http://example.com/webhook2",
            },
        ]
        response_data = {"webhooks": webhook_data}
        cast(
            "Mock", mock_async_base_client._get
        ).return_value.json.return_value = response_data

        result = await webhooks_api.list("acc_00009237aqC8c5umZmrRdh")

        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/webhooks", params={"account_id": "acc_00009237aqC8c5umZmrRdh"}
        )
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(webhook, Webhook) for webhook in result)
        assert result[0].id == "webhook_000091yhhOmrXQaVZ1Irsv"
        assert result[1].id == "webhook_000091yhhOmrXQaVZ1Irsw"

    @pytest.mark.asyncio
    async def test_list_empty(
        self,
        webhooks_api: AsyncWebhooksAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test list webhooks with empty result.

        Args:
            webhooks_api: Async webhooks API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        response_data: dict[str, Any] = {"webhooks": []}
        cast(
            "Mock", mock_async_base_client._get
        ).return_value.json.return_value = response_data

        result = await webhooks_api.list("acc_00009237aqC8c5umZmrRdh")

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete(
        self,
        webhooks_api: AsyncWebhooksAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test delete webhook.

        Args:
            webhooks_api: Async webhooks API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        await webhooks_api.delete("webhook_000091yhhOmrXQaVZ1Irsv")

        cast("Mock", mock_async_base_client._delete).assert_called_once_with(
            "/webhooks/webhook_000091yhhOmrXQaVZ1Irsv"
        )
