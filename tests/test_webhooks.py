"""Tests for webhooks API."""

from typing import Any

from monzoh.models import Webhook
from monzoh.webhooks import WebhooksAPI


class TestWebhooksAPI:
    """Test WebhooksAPI."""

    def test_init(self, monzo_sync_client: Any) -> None:
        """Test client initialization."""
        api = WebhooksAPI(monzo_sync_client._base_client)
        assert api.client is monzo_sync_client._base_client

    def test_register(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test register webhook."""
        webhook_data = {
            "id": "webhook_000091yhhOmrXQaVZ1Irsv",
            "account_id": "acc_00009237aqC8c5umZmrRdh",
            "url": "http://example.com/webhook",
        }
        response_data = {"webhook": webhook_data}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._post.return_value = mock_response

        api = WebhooksAPI(monzo_sync_client._base_client)
        result = api.register(
            "acc_00009237aqC8c5umZmrRdh", "http://example.com/webhook"
        )

        assert isinstance(result, Webhook)
        assert result.id == "webhook_000091yhhOmrXQaVZ1Irsv"
        assert result.account_id == "acc_00009237aqC8c5umZmrRdh"
        assert result.url == "http://example.com/webhook"

    def test_list(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test list webhooks."""
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
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._get.return_value = mock_response

        api = WebhooksAPI(monzo_sync_client._base_client)
        result = api.list("acc_00009237aqC8c5umZmrRdh")

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(webhook, Webhook) for webhook in result)
        assert result[0].id == "webhook_000091yhhOmrXQaVZ1Irsv"
        assert result[1].id == "webhook_000091yhhOmrXQaVZ1Irsw"

    def test_list_empty(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test list webhooks with empty result."""
        response_data: dict[str, Any] = {"webhooks": []}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._get.return_value = mock_response

        api = WebhooksAPI(monzo_sync_client._base_client)
        result = api.list("acc_00009237aqC8c5umZmrRdh")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_delete(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test delete webhook."""
        mock_response = mock_httpx_response(json_data={})
        monzo_sync_client._base_client._delete.return_value = mock_response

        api = WebhooksAPI(monzo_sync_client._base_client)
        api.delete("webhook_000091yhhOmrXQaVZ1Irsv")
        monzo_sync_client._base_client._delete.assert_called_once_with(
            "/webhooks/webhook_000091yhhOmrXQaVZ1Irsv"
        )
