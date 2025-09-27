"""Tests for attachments API."""

import tempfile
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from monzoh.api.attachments import AttachmentsAPI
from monzoh.client import MonzoClient
from monzoh.models import Attachment


class TestAttachmentsAPI:
    """Test AttachmentsAPI."""

    def test_init(self, monzo_client: MonzoClient) -> None:
        """Test client initialization.

        Args:
            monzo_client: Monzo client fixture.
        """
        api = AttachmentsAPI(monzo_client._base_client)
        assert api.client is monzo_client._base_client

    @patch("httpx.Client")
    def test_upload(
        self,
        mock_httpx_client_class: Any,
        monzo_client: MonzoClient,
        mock_response: Mock,
    ) -> None:
        """Test simplified upload process.

        Args:
            mock_httpx_client_class: Mock httpx client class fixture.
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
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

        upload_response = mock_response(json_data=upload_data)
        register_response = mock_response(json_data=register_response_data)
        cast("Mock", monzo_client._base_client._post).side_effect = [
            upload_response,
            register_response,
        ]

        mock_client = Mock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        api = AttachmentsAPI(monzo_client._base_client)
        file_data = b"test file content"
        result = api.upload(
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
            headers={
                "Content-Type": "image/jpeg",
                "Content-Length": str(len(file_data)),
            },
        )

    @patch("httpx.Client")
    def test_upload_with_file_path(
        self,
        mock_httpx_client_class: Any,
        monzo_client: MonzoClient,
        mock_response: Mock,
    ) -> None:
        """Test upload with file path.

        Args:
            mock_httpx_client_class: Mock httpx client class fixture.
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
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

            upload_response = mock_response(json_data=upload_data)
            register_response = mock_response(json_data=register_response_data)
            cast("Mock", monzo_client._base_client._post).side_effect = [
                upload_response,
                register_response,
            ]

            mock_client = Mock()
            mock_httpx_client_class.return_value.__enter__.return_value = mock_client

            api = AttachmentsAPI(monzo_client._base_client)
            result = api.upload(
                transaction_id="tx_00008zIcpb1TB4yeIFXMzx", file_path=tmp_file_path
            )

            assert isinstance(result, Attachment)
            assert result.id == attachment_data["id"]
            assert result.external_id == attachment_data["external_id"]

            mock_client.put.assert_called_once_with(
                "https://s3.amazonaws.com/upload",
                content=test_content,
                headers={
                    "Content-Type": "image/jpeg",
                    "Content-Length": str(len(test_content)),
                },
            )

            expected_file_name = Path(tmp_file_path).name
            cast("Mock", monzo_client._base_client._post).assert_any_call(
                "/attachment/upload",
                data={
                    "file_name": expected_file_name,
                    "file_type": "image/jpeg",
                    "content_length": str(len(test_content)),
                },
            )

        finally:
            Path(tmp_file_path).unlink()

    def test_upload_validation_error(self, monzo_client: MonzoClient) -> None:
        """Test upload validation when neither file_path nor required args provided.

        Args:
            monzo_client: Monzo client fixture.
        """
        api = AttachmentsAPI(monzo_client._base_client)

        with pytest.raises(ValueError, match="Either file_path must be provided"):
            api.upload(transaction_id="tx_123")

    def test_private_register(
        self,
        monzo_client: MonzoClient,
        mock_response: Mock,
    ) -> None:
        """Test private register method.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
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
        mock_response = mock_response(json_data=response_data)
        cast("Mock", monzo_client._base_client._post).return_value = mock_response

        api = AttachmentsAPI(monzo_client._base_client)
        result = api._register(
            "tx_00008zIcpb1TB4yeIFXMzx",
            "https://s3.amazonaws.com/...",
            "image/jpeg",
        )

        assert isinstance(result, Attachment)
        assert result.id == attachment_data["id"]
        assert result.external_id == attachment_data["external_id"]

    def test_deregister(
        self,
        monzo_client: MonzoClient,
        mock_response: Mock,
    ) -> None:
        """Test deregister.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
        """
        mock_response = mock_response(json_data={})
        cast("Mock", monzo_client._base_client._post).return_value = mock_response

        api = AttachmentsAPI(monzo_client._base_client)
        api.deregister("attach_00009238aOZ8rp29FlJDQc")

    @patch("httpx.Client")
    def test_private_upload_file_to_url(
        self, mock_httpx_client_class: Any, monzo_client: MonzoClient
    ) -> None:
        """Test private file upload to URL method.

        Args:
            mock_httpx_client_class: Mock httpx client class fixture.
            monzo_client: Monzo client fixture.
        """
        mock_client = Mock()
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        api = AttachmentsAPI(monzo_client._base_client)
        file_data = b"test file content"

        api._upload_file_to_url(
            "https://s3.amazonaws.com/upload", file_data, "application/octet-stream"
        )
        mock_client.put.assert_called_once_with(
            "https://s3.amazonaws.com/upload",
            content=file_data,
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_data)),
            },
        )
