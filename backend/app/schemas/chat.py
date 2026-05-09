import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class MessageAttachmentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    attachment_type: str
    download_url: str


class AttachmentUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    attachment_type: str
    download_url: str


class ChatRequest(BaseModel):
    thread_id: uuid.UUID
    message: str = ""
    attachment_ids: list[uuid.UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payload(self) -> "ChatRequest":
        if self.message.strip() or self.attachment_ids:
            return self
        raise ValueError("message or attachment_ids is required")


class MessageResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    attachments: list[MessageAttachmentResponse] = Field(default_factory=list)


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    thread_id: uuid.UUID | None = None


class ImageGenerationResponse(BaseModel):
    url: str
    filename: str
    mime_type: str
    original_prompt: str
    size_bytes: int
