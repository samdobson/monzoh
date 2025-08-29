"""Async attachments API endpoints."""

from typing import BinaryIO

from ..core.async_base import BaseAsyncClient
from ..models import Attachment, AttachmentResponse, AttachmentUpload


class AsyncAttachmentsAPI:
    """Async attachments API client."""

    def __init__(self, client: BaseAsyncClient) -> None:
        """Initialize async attachments API.

        Args:
            client: Base async API client
        """
        self.client = client

    async def upload(
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

    async def register(
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

    async def upload_file_to_url(self, upload_url: str, file_data: BinaryIO) -> None:
        """Upload file data to the provided upload URL.

        This is a helper method to upload the actual file content to the URL
        returned by the upload() method.

        Args:
            upload_url: Upload URL from upload() response
            file_data: File binary data

        Returns:
            None
        """
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(upload_url, content=file_data.read())
