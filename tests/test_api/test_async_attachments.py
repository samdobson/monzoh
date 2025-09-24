"""Tests for async attachments API."""

import tempfile
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from monzoh.api.async_attachments import AsyncAttachmentsAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Attachment


class TestAsyncAttachmentsAPI:
    """Test async attachments API."""

    @pytest.fixture
    def attachments_api(
        self, mock_async_base_client: BaseAsyncClient
    ) -> AsyncAttachmentsAPI:
        """Create async attachments API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncAttachmentsAPI instance.
        """
        return AsyncAttachmentsAPI(mock_async_base_client)

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_upload(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test simplified upload process.

        Args:
            mock_httpx_client_class: Mock httpx async client class fixture.
            attachments_api: Async attachments API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        upload_data = {
            "upload_url": "https://s3.amazonaws.com/upload",
            "file_url": "https://s3.amazonaws.com/file",
        }
        attachment_data = {
            "id": "attach_00009238aOZ8rp29FlJDQc",
            "user_id": "user_00009237aqC8c5umZmrRdh",
            "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "file_url": "https://s3.amazonaws.com/file",
            "file_type": "image/jpeg",
            "created": "2015-11-12T18:37:02Z",
        }
        register_response_data = {"attachment": attachment_data}

        upload_response = Mock()
        upload_response.json.return_value = upload_data
        register_response = Mock()
        register_response.json.return_value = register_response_data

        async def mock_post_side_effect(*args: Any, **_kwargs: Any) -> Mock:
            if args[0] == "/attachment/upload":
                return upload_response
            if args[0] == "/attachment/register":
                return register_response
            return Mock()

        cast("Mock", mock_async_base_client._post).side_effect = mock_post_side_effect

        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_httpx_client_class.return_value.__aenter__.return_value = mock_client

        file_data = b"test file content"
        result = await attachments_api.upload(
            transaction_id="tx_00008zIcpb1TB4yeIFXMzx",
            file_name="test.jpg",
            file_type="image/jpeg",
            file_data=file_data,
        )

        assert isinstance(result, Attachment)
        assert result.id == attachment_data["id"]
        assert result.external_id == attachment_data["external_id"]

        mock_client.put.assert_called_once_with(
            "https://s3.amazonaws.com/upload",
            content=file_data,
            headers={"Content-Type": "image/jpeg", "Content-Length": "17"},
        )

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_upload_with_file_path(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test upload with file path.

        Args:
            mock_httpx_client_class: Mock httpx async client class fixture.
            attachments_api: Async attachments API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".jpg", delete=False
        ) as tmp_file:
            test_content = b"test image content"
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name

        try:
            upload_data = {
                "upload_url": "https://s3.amazonaws.com/upload",
                "file_url": "https://s3.amazonaws.com/file",
            }
            attachment_data = {
                "id": "attach_00009238aOZ8rp29FlJDQc",
                "user_id": "user_00009237aqC8c5umZmrRdh",
                "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
                "file_url": "https://s3.amazonaws.com/file",
                "file_type": "image/jpeg",
                "created": "2015-11-12T18:37:02Z",
            }
            register_response_data = {"attachment": attachment_data}

            upload_response = Mock()
            upload_response.json.return_value = upload_data
            register_response = Mock()
            register_response.json.return_value = register_response_data

            async def mock_post_side_effect(*args: Any, **_kwargs: Any) -> Mock:
                if args[0] == "/attachment/upload":
                    return upload_response
                if args[0] == "/attachment/register":
                    return register_response
                return Mock()

            cast(
                "Mock", mock_async_base_client._post
            ).side_effect = mock_post_side_effect

            mock_client = Mock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_client.put = AsyncMock(return_value=mock_response)
            mock_httpx_client_class.return_value.__aenter__.return_value = mock_client

            result = await attachments_api.upload(
                transaction_id="tx_00008zIcpb1TB4yeIFXMzx", file_path=tmp_file_path
            )

            assert isinstance(result, Attachment)
            assert result.id == attachment_data["id"]
            assert result.external_id == attachment_data["external_id"]

            mock_client.put.assert_called_once_with(
                "https://s3.amazonaws.com/upload",
                content=test_content,
                headers={"Content-Type": "image/jpeg", "Content-Length": "18"},
            )

            expected_file_name = Path(tmp_file_path).name

            actual_calls = cast("Mock", mock_async_base_client._post).call_args_list
            assert len(actual_calls) >= 1
            assert actual_calls[0][0] == ("/attachment/upload",)
            assert actual_calls[0][1]["data"]["file_name"] == expected_file_name
            assert actual_calls[0][1]["data"]["file_type"] == "image/jpeg"

        finally:
            Path(tmp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_upload_validation_error(
        self, attachments_api: AsyncAttachmentsAPI
    ) -> None:
        """Test upload validation when neither file_path nor required args provided.

        Args:
            attachments_api: Async attachments API fixture.
        """
        with pytest.raises(ValueError, match="Either file_path must be provided"):
            await attachments_api.upload(transaction_id="tx_123")

    @pytest.mark.asyncio
    async def test_private_register(
        self,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test private register method.

        Args:
            attachments_api: Async attachments API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        attachment_data = {
            "id": "attach_00009238aOZ8rp29FlJDQc",
            "user_id": "user_00009237aqC8c5umZmrRdh",
            "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "file_url": "https://s3.amazonaws.com/...",
            "file_type": "image/jpeg",
            "created": "2015-11-12T18:37:02Z",
        }
        response_data = {"attachment": attachment_data}
        response_mock = Mock()
        response_mock.json.return_value = response_data

        async def mock_post(*_args: Any, **_kwargs: Any) -> Mock:
            return response_mock

        cast("Mock", mock_async_base_client._post).side_effect = mock_post

        result = await attachments_api._register(
            "tx_00008zIcpb1TB4yeIFXMzx",
            "https://s3.amazonaws.com/...",
            "image/jpeg",
        )

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
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
        """Test deregister.

        Args:
            attachments_api: Async attachments API fixture.
            mock_async_base_client: Mock async base client fixture.
        """
        cast("Mock", mock_async_base_client._post).return_value = AsyncMock()

        await attachments_api.deregister("attach_00009238aOZ8rp29FlJDQc")

        cast("Mock", mock_async_base_client._post).assert_called_once_with(
            "/attachment/deregister", data={"id": "attach_00009238aOZ8rp29FlJDQc"}
        )

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_private_upload_file_to_url(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
    ) -> None:
        """Test private file upload to URL method.

        Args:
            mock_httpx_client_class: Mock httpx async client class fixture.
            attachments_api: Async attachments API fixture.
        """
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_httpx_client_class.return_value.__aenter__.return_value = mock_client

        file_data = b"test file content"

        await attachments_api._upload_file_to_url(
            "https://s3.amazonaws.com/upload", file_data, "image/jpeg"
        )

        mock_client.put.assert_called_once_with(
            "https://s3.amazonaws.com/upload",
            content=file_data,
            headers={"Content-Type": "image/jpeg", "Content-Length": "17"},
        )
        mock_response.raise_for_status.assert_called_once()
