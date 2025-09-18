"""Async attachments API endpoints."""

from pathlib import Path

from ..core.async_base import BaseAsyncClient
from ..models import Attachment, AttachmentResponse, AttachmentUpload
from ..utils import infer_file_type, read_file_data


class AsyncAttachmentsAPI:
    """Async attachments API client.

    Args:
        client: Base async API client
    """

    def __init__(self, client: BaseAsyncClient) -> None:
        self.client = client

    async def upload(
        self,
        transaction_id: str,
        file_path: str | Path | None = None,
        file_name: str | None = None,
        file_type: str | None = None,
        file_data: bytes | None = None,
    ) -> Attachment:
        """Upload a file and attach it to a transaction in a single step.

        Args:
            transaction_id: Transaction ID to attach to
            file_path: Path to file (if provided, file_name, file_type, and file_data
                are inferred)
            file_name: Name of the file (required if file_path not provided)
            file_type: MIME type of the file (inferred from path if not provided)
            file_data: File binary data (read from path if not provided)

        Returns:
            Registered attachment

        Raises:
            ValueError: If neither file_path nor (file_name and file_data) are provided
        """
        if file_path:
            path = Path(file_path)
            actual_file_name = file_name or path.name
            actual_file_type = file_type or infer_file_type(path)
            actual_file_data = read_file_data(path)
        elif file_name and file_data is not None:
            actual_file_name = file_name
            actual_file_type = file_type or "application/octet-stream"
            actual_file_data = file_data
        else:
            raise ValueError(
                "Either file_path must be provided, or both file_name and file_data "
                "must be provided"
            )

        upload_info = await self._get_upload_url(
            file_name=actual_file_name,
            file_type=actual_file_type,
            content_length=len(actual_file_data),
        )

        await self._upload_file_to_url(
            upload_url=upload_info.upload_url,
            file_data=actual_file_data,
            file_type=actual_file_type,
        )

        attachment = await self._register(
            external_id=transaction_id,
            file_url=upload_info.file_url,
            file_type=actual_file_type,
        )
        return attachment

    async def _get_upload_url(
        self, file_name: str, file_type: str, content_length: int
    ) -> AttachmentUpload:
        """Get upload URL for an attachment.

        Args:
            file_name: Name of the file
            file_type: MIME type of the file
            content_length: Size of the file in bytes

        Returns:
            Upload URLs
        """
        data = {
            "file_name": file_name,
            "file_type": file_type,
            "content_length": str(content_length),
        }

        response = await self.client._post("/attachment/upload", data=data)
        return AttachmentUpload(**response.json())

    async def _register(
        self, external_id: str, file_url: str, file_type: str
    ) -> Attachment:
        """Register an attachment with a transaction.

        Args:
            external_id: Transaction ID to attach to
            file_url: URL of the uploaded file
            file_type: MIME type of the file

        Returns:
            Registered attachment
        """
        data = {
            "external_id": external_id,
            "file_url": file_url,
            "file_type": file_type,
        }

        response = await self.client._post("/attachment/register", data=data)
        attachment_response = AttachmentResponse(**response.json())
        return attachment_response.attachment

    async def deregister(self, attachment_id: str) -> None:
        """Remove an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            None
        """
        data = {"id": attachment_id}

        await self.client._post("/attachment/deregister", data=data)

    async def _upload_file_to_url(
        self, upload_url: str, file_data: bytes, file_type: str
    ) -> None:
        """Upload file data to the provided upload URL.

        Args:
            upload_url: Upload URL from upload response
            file_data: File binary data
            file_type: MIME type of the file

        Returns:
            None
        """
        import httpx

        headers = {
            "Content-Type": file_type,
            "Content-Length": str(len(file_data)),
        }

        async with httpx.AsyncClient() as client:
            response = await client.put(upload_url, content=file_data, headers=headers)
            response.raise_for_status()
