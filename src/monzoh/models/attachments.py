"""Attachment-related models."""

from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentUpload(BaseModel):
    """Upload attachment response."""

    file_url: str = Field(
        ..., description="URL where the file will be accessible after upload"
    )
    upload_url: str = Field(
        ..., description="Temporary URL to POST the file to for upload"
    )


class Attachment(BaseModel):
    """Represents an attachment."""

    id: str = Field(..., description="Unique attachment identifier")
    user_id: str = Field(..., description="ID of the user who owns the attachment")
    external_id: str = Field(
        ..., description="ID of the transaction the attachment is associated with"
    )
    file_url: str = Field(
        ..., description="URL where the attachment file is accessible"
    )
    file_type: str = Field(
        ..., description="MIME type of the attachment (e.g., 'image/png')"
    )
    created: datetime = Field(..., description="Attachment creation timestamp")


class AttachmentResponse(BaseModel):
    """Attachment response."""

    attachment: Attachment = Field(..., description="Attachment object")
