"""Tests for attachments API."""

from io import BytesIO
from typing import Any
from unittest.mock import Mock, patch

from monzoh.attachments import AttachmentsAPI
from monzoh.models import Attachment, AttachmentUpload


class TestAttachmentsAPI:
    """Test AttachmentsAPI."""

    def test_init(self, monzo_sync_client: Any) -> None:
        """Test client initialization."""
        api = AttachmentsAPI(monzo_sync_client._base_client)
        assert api.client is monzo_sync_client._base_client

    def test_upload(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test upload."""
        upload_data = {
            "upload_url": "https://s3.amazonaws.com/...",
            "file_url": "https://s3.amazonaws.com/...",
        }
        mock_response = mock_httpx_response(json_data=upload_data)
        monzo_sync_client._base_client._post.return_value = mock_response

        api = AttachmentsAPI(monzo_sync_client._base_client)
        result = api.upload("test.jpg", "image/jpeg", 1024)

        assert isinstance(result, AttachmentUpload)
        assert result.upload_url == upload_data["upload_url"]
        assert result.file_url == upload_data["file_url"]

    def test_register(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test register."""
        attachment_data = {
            "id": "attach_00009238aOZ8rp29FlJDQc",
            "user_id": "user_00009237aqC8c5umZmrRdh",
            "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "file_url": "https://s3.amazonaws.com/...",
            "file_type": "image/jpeg",
            "created": "2015-11-12T18:37:02Z",
        }
        response_data = {"attachment": attachment_data}
        mock_response = mock_httpx_response(json_data=response_data)
        monzo_sync_client._base_client._post.return_value = mock_response

        api = AttachmentsAPI(monzo_sync_client._base_client)
        result = api.register(
            "tx_00008zIcpb1TB4yeIFXMzx",
            "https://s3.amazonaws.com/...",
            "image/jpeg",
        )

        assert isinstance(result, Attachment)
        assert result.id == attachment_data["id"]
        assert result.external_id == attachment_data["external_id"]

    def test_deregister(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
    ) -> None:
        """Test deregister."""
        mock_response = mock_httpx_response(json_data={})
        monzo_sync_client._base_client._post.return_value = mock_response

        api = AttachmentsAPI(monzo_sync_client._base_client)
        api.deregister("attach_00009238aOZ8rp29FlJDQc")

    @patch("httpx.Client")
    def test_upload_file_to_url(
        self, mock_httpx_client_class: Any, monzo_sync_client: Any
    ) -> None:
        """Test file upload to URL."""
        mock_client = Mock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        api = AttachmentsAPI(monzo_sync_client._base_client)
        file_data = BytesIO(b"test file content")

        api.upload_file_to_url("https://s3.amazonaws.com/upload", file_data)
        mock_client.post.assert_called_once_with(
            "https://s3.amazonaws.com/upload", content=b"test file content"
        )
