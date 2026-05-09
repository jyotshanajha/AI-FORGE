import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.thread import ThreadCreateRequest, ThreadResponse, ThreadUpdateRequest
from app.services.thread_service import ThreadService


router = APIRouter()


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ThreadResponse]:
    rows = await ThreadService.list_threads(db, current_user)
    return [ThreadResponse(id=t.id, title=t.title, created_at=t.created_at, updated_at=t.updated_at) for t in rows]


@router.post("", response_model=ThreadResponse)
async def create_thread(
    payload: ThreadCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreadResponse:
    thread = await ThreadService.create_thread(db, current_user, payload.title)
    return ThreadResponse(id=thread.id, title=thread.title, created_at=thread.created_at, updated_at=thread.updated_at)


@router.patch("/{thread_id}", response_model=ThreadResponse)
async def rename_thread(
    thread_id: uuid.UUID,
    payload: ThreadUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreadResponse:
    thread = await ThreadService.get_thread_or_404(db, current_user, thread_id)
    thread = await ThreadService.update_thread_title(db, thread, payload.title)
    return ThreadResponse(id=thread.id, title=thread.title, created_at=thread.created_at, updated_at=thread.updated_at)


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    thread = await ThreadService.get_thread_or_404(db, current_user, thread_id)
    await ThreadService.delete_thread(db, thread)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
