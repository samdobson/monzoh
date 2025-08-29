"""Tests for async attachments API."""

from io import BytesIO
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from monzoh.api.async_attachments import AsyncAttachmentsAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Attachment, AttachmentUpload


class TestAsyncAttachmentsAPI:
    """Test async attachments API."""

    @pytest.fixture
    def attachments_api(
        self, mock_async_base_client: BaseAsyncClient
    ) -> AsyncAttachmentsAPI:
        """Create async attachments API instance."""
        return AsyncAttachmentsAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_upload(
        self,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test upload."""
        upload_data = {
            "upload_url": "https://s3.amazonaws.com/...",
            "file_url": "https://s3.amazonaws.com/...",
        }
        cast(Mock, mock_async_base_client._post).return_value.json.return_value = (
            upload_data
        )

        result = await attachments_api.upload("test.jpg", "image/jpeg", 1024)

        cast(Mock, mock_async_base_client._post).assert_called_once_with(
            "/attachment/upload",
            data={
                "file_name": "test.jpg",
                "file_type": "image/jpeg",
                "content_length": "1024",
            },
        )
        assert isinstance(result, AttachmentUpload)
        assert result.upload_url == upload_data["upload_url"]
        assert result.file_url == upload_data["file_url"]

    @pytest.mark.asyncio
    async def test_register(
        self,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
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
        cast(Mock, mock_async_base_client._post).return_value.json.return_value = (
            response_data
        )

        result = await attachments_api.register(
            "tx_00008zIcpb1TB4yeIFXMzx",
            "https://s3.amazonaws.com/...",
            "image/jpeg",
        )

        cast(Mock, mock_async_base_client._post).assert_called_once_with(
            "/attachment/register",
            data={
                "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
                "file_url": "https://s3.amazonaws.com/...",
                "file_type": "image/jpeg",
            },
        )
        assert isinstance(result, Attachment)
        assert result.id == attachment_data["id"]
        assert result.external_id == attachment_data["external_id"]

    @pytest.mark.asyncio
    async def test_deregister(
        self,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test deregister."""
        await attachments_api.deregister("attach_00009238aOZ8rp29FlJDQc")

        cast(Mock, mock_async_base_client._post).assert_called_once_with(
            "/attachment/deregister", data={"id": "attach_00009238aOZ8rp29FlJDQc"}
        )

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_upload_file_to_url(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
    ) -> None:
        """Test file upload to URL."""
        mock_client = Mock()
        mock_client.post = AsyncMock()
        mock_httpx_client_class.return_value.__aenter__.return_value = mock_client

        file_data = BytesIO(b"test file content")

        await attachments_api.upload_file_to_url(
            "https://s3.amazonaws.com/upload", file_data
        )

        mock_client.post.assert_called_once_with(
            "https://s3.amazonaws.com/upload", content=b"test file content"
        )
