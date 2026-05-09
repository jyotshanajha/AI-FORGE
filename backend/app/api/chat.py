import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import AttachmentUploadResponse, ChatRequest, ImageGenerationRequest, ImageGenerationResponse, MessageResponse, MessageAttachmentResponse
from app.services.attachment_service import AttachmentService
from app.services.chat_service import ChatService
from app.services.image_service import get_image_service


router = APIRouter()


@router.get("/{thread_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    thread_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    rows = await ChatService.list_messages(db, current_user, thread_id)
    attachment_map = AttachmentService.get_attachments_for_message_ids(
        current_user.id,
        [row.id for row in rows],
    )
    return [
        MessageResponse(
            id=row.id,
            thread_id=row.thread_id,
            role=row.role,
            content=row.content,
            created_at=row.created_at,
            attachments=[MessageAttachmentResponse(**item) for item in attachment_map.get(row.id, [])],
        )
        for row in rows
    ]


@router.post("/attachments", response_model=AttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
) -> AttachmentUploadResponse:
    data = await AttachmentService.upload_attachment(current_user.id, file)
    
    # Retrieve stored path from the store for PDF ingestion
    from app.services.fallback_store import get_store
    store = get_store()
    attachment_id = str(data["id"])
    by_id = store.get("attachments_by_id", {})
    metadata = by_id.get(attachment_id, {})
    stored_path = metadata.get("stored_path")
    
    # Trigger PDF ingestion in background if it's a PDF
    if stored_path:
        background_tasks.add_task(
            AttachmentService.ingest_pdf_if_needed,
            current_user.id,
            current_user.email,
            uuid.UUID(attachment_id),
            data["mime_type"],
            data["filename"],
            stored_path,
        )
    
    return AttachmentUploadResponse(**data)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    resolved = AttachmentService.get_download_path(current_user.id, attachment_id)
    if not resolved:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Attachment not found"})

    stored_path, filename, mime_type = resolved
    return FileResponse(path=stored_path, media_type=mime_type, filename=filename)


@router.get("/attachments/generated/{user_id}/{filename}")
async def download_generated_image(
    user_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download a generated image."""
    from pathlib import Path
    from app.core.config import settings
    
    # Verify user is accessing their own generated images
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Access denied"})
    
    # Construct safe file path
    file_path = Path(settings.UPLOAD_DIR) / "generated" / user_id / filename
    
    # Verify the file exists and is within the expected directory
    try:
        file_path = file_path.resolve()
        expected_dir = (Path(settings.UPLOAD_DIR) / "generated" / user_id).resolve()
        if not str(file_path).startswith(str(expected_dir)):
            raise HTTPException(status_code=403, detail={"error": "forbidden", "message": "Invalid file path"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "invalid_path", "message": str(e)})
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Generated image not found"})
    
    return FileResponse(path=str(file_path), media_type="image/png", filename=filename)


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    async def event_generator() -> object:
        async for chunk in ChatService.stream_reply(
            db,
            current_user,
            payload.thread_id,
            payload.message,
            payload.attachment_ids,
        ):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(
    payload: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
) -> ImageGenerationResponse:
    """Generate an image using Gemini image generation model."""
    try:
        image_service = get_image_service()
        result = await image_service.generate_image(
            prompt=payload.prompt,
            user_email=current_user.email,
            user_id=str(current_user.id),
        )
        return ImageGenerationResponse(**result)
    except Exception as e:
        error_msg = str(e)
        print(f"Image generation error: {error_msg}")
        if "connection" in error_msg.lower() or "connect" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={"error": "service_unavailable", "message": "Image generation service is unavailable. Please check VPN connection."},
            )
        raise HTTPException(
            status_code=502,
            detail={"error": "image_generation_failed", "message": f"Image generation failed: {error_msg}"},
        )
