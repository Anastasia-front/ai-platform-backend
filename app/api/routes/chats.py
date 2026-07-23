from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_chat_repository,
    get_chat_update_service,
    get_current_user,
    get_owned_chat,
    get_owned_project,
)
from app.models import Chat, Project, User
from app.repositories import ChatRepository
from app.schemas import ChatCreate, ChatResponse, ChatUpdate
from app.services import ChatUpdateService

router = APIRouter()

# -------------------------------------------------
# CREATE CHAT
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    payload: ChatCreate,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    service: ChatUpdateService = Depends(get_chat_update_service),
):
    return await service.create(
        db=db,
        payload=payload,
        project=project,
    )

# -------------------------------------------------
# GET SINGLE CHAT
# -------------------------------------------------
@router.get(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def get_chat(
    chat: Chat = Depends(get_owned_chat),
):
    return chat


# -------------------------------------------------
# UPDATE CHAT
# -------------------------------------------------
@router.patch(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def update_chat(
    payload: ChatUpdate,
    db: AsyncSession = Depends(get_db),
    chat: Chat = Depends(get_owned_chat),
    service: ChatUpdateService = Depends(get_chat_update_service),
):
    return await service.update(
        db=db,
        chat=chat,
        payload=payload,
    )

# -------------------------------------------------
# GET PROJECT CHATS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/chats",
    response_model=List[ChatResponse],
)
async def get_project_chats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    project: Project = Depends(get_owned_project),
    chats: ChatRepository = Depends(
        get_chat_repository
    ),
):
    return await chats.list_for_project(
        db,
        project.id,
        user.id,
    )

# -------------------------------------------------
# DELETE CHAT
# -------------------------------------------------
@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat(
    db: AsyncSession = Depends(get_db),
    chat: Chat = Depends(get_owned_chat),
    service: ChatUpdateService = Depends(get_chat_update_service),
):
    await service.delete(db, chat)
