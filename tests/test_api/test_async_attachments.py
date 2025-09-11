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
        """Create async attachments API instance."""
        return AsyncAttachmentsAPI(mock_async_base_client)

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_upload(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test simplified upload process."""
        # Mock the upload URL response
        upload_data = {
            "upload_url": "https://s3.amazonaws.com/upload",
            "file_url": "https://s3.amazonaws.com/file",
        }
        # Mock the register response
        attachment_data = {
            "id": "attach_00009238aOZ8rp29FlJDQc",
            "user_id": "user_00009237aqC8c5umZmrRdh",
            "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
            "file_url": "https://s3.amazonaws.com/file",
            "file_type": "image/jpeg",
            "created": "2015-11-12T18:37:02Z",
        }
        register_response_data = {"attachment": attachment_data}

        # Setup mock responses for the two API calls
        upload_response = Mock()
        upload_response.json.return_value = upload_data
        register_response = Mock()
        register_response.json.return_value = register_response_data

        # Create async mocks that return the responses when awaited
        async def mock_post_side_effect(*args: Any, **kwargs: Any) -> Mock:
            if args[0] == "/attachment/upload":
                return upload_response
            elif args[0] == "/attachment/register":
                return register_response
            return Mock()

        cast(Mock, mock_async_base_client._post).side_effect = mock_post_side_effect

        # Mock httpx async client for file upload
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

        # Verify the result is an attachment
        assert isinstance(result, Attachment)
        assert result.id == attachment_data["id"]
        assert result.external_id == attachment_data["external_id"]

        # Verify file upload was called
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
        """Test upload with file path."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".jpg", delete=False
        ) as tmp_file:
            test_content = b"test image content"
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name

        try:
            # Mock the upload URL response
            upload_data = {
                "upload_url": "https://s3.amazonaws.com/upload",
                "file_url": "https://s3.amazonaws.com/file",
            }
            # Mock the register response
            attachment_data = {
                "id": "attach_00009238aOZ8rp29FlJDQc",
                "user_id": "user_00009237aqC8c5umZmrRdh",
                "external_id": "tx_00008zIcpb1TB4yeIFXMzx",
                "file_url": "https://s3.amazonaws.com/file",
                "file_type": "image/jpeg",
                "created": "2015-11-12T18:37:02Z",
            }
            register_response_data = {"attachment": attachment_data}

            # Setup mock responses for the two API calls
            upload_response = Mock()
            upload_response.json.return_value = upload_data
            register_response = Mock()
            register_response.json.return_value = register_response_data

            # Create async mocks that return the responses when awaited
            async def mock_post_side_effect(*args: Any, **kwargs: Any) -> Mock:
                if args[0] == "/attachment/upload":
                    return upload_response
                elif args[0] == "/attachment/register":
                    return register_response
                return Mock()

            cast(Mock, mock_async_base_client._post).side_effect = mock_post_side_effect

            # Mock httpx async client for file upload
            mock_client = Mock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_client.put = AsyncMock(return_value=mock_response)
            mock_httpx_client_class.return_value.__aenter__.return_value = mock_client

            result = await attachments_api.upload(
                transaction_id="tx_00008zIcpb1TB4yeIFXMzx", file_path=tmp_file_path
            )

            # Verify the result is an attachment
            assert isinstance(result, Attachment)
            assert result.id == attachment_data["id"]
            assert result.external_id == attachment_data["external_id"]

            # Verify file upload was called with correct content
            mock_client.put.assert_called_once_with(
                "https://s3.amazonaws.com/upload",
                content=test_content,
                headers={"Content-Type": "image/jpeg", "Content-Length": "18"},
            )

            # Verify the API calls were made with inferred values
            expected_file_name = Path(tmp_file_path).name

            # Check the first call (upload URL request)
            actual_calls = cast(Mock, mock_async_base_client._post).call_args_list
            assert len(actual_calls) >= 1
            assert actual_calls[0][0] == ("/attachment/upload",)
            assert actual_calls[0][1]["data"]["file_name"] == expected_file_name
            assert actual_calls[0][1]["data"]["file_type"] == "image/jpeg"

        finally:
            # Clean up temporary file
            Path(tmp_file_path).unlink()

    @pytest.mark.asyncio
    async def test_upload_validation_error(
        self, attachments_api: AsyncAttachmentsAPI
    ) -> None:
        """Test upload validation when neither file_path nor required args provided."""
        with pytest.raises(ValueError, match="Either file_path must be provided"):
            await attachments_api.upload(
                transaction_id="tx_123"
            )  # Missing required args

    @pytest.mark.asyncio
    async def test_private_register(
        self,
        attachments_api: AsyncAttachmentsAPI,
        mock_async_base_client: BaseAsyncClient,
    ) -> None:
        """Test private register method."""
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

        # Create async mock that returns the response when awaited
        async def mock_post(*args: Any, **kwargs: Any) -> Mock:
            return response_mock

        cast(Mock, mock_async_base_client._post).side_effect = mock_post

        result = await attachments_api._register(
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
        cast(Mock, mock_async_base_client._post).return_value = AsyncMock()

        await attachments_api.deregister("attach_00009238aOZ8rp29FlJDQc")

        cast(Mock, mock_async_base_client._post).assert_called_once_with(
            "/attachment/deregister", data={"id": "attach_00009238aOZ8rp29FlJDQc"}
        )

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_private_upload_file_to_url(
        self,
        mock_httpx_client_class: Any,
        attachments_api: AsyncAttachmentsAPI,
    ) -> None:
        """Test private file upload to URL method."""
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
