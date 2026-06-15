from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_chat_repository,
    get_current_user,
    get_owned_chat,
    get_owned_project,
    get_project_repository,
)
from app.models import Chat, User
from app.repositories import ChatRepository, ProjectRepository
from app.schemas import ChatCreate, ChatResponse

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
    project = Depends(get_owned_project),
    projects: ProjectRepository = Depends(
        get_project_repository
    ),
):
    chat = Chat(
        project_id=project.id,
        title=payload.title,
        agent_name=payload.agent_name,
    )

    await projects.create(
        db,
        chat
    )
    await db.commit()
    await db.refresh(chat)

    return chat

# -------------------------------------------------
# GET SINGLE CHAT
# -------------------------------------------------
@router.get(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def get_chat(
    chat = Depends(get_owned_chat),
):
    return chat

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
    project = Depends(get_owned_project),
    chats: ChatRepository = Depends(
        get_chat_repository
    ),
):
    return await chats.get_for_user(
        db,
        project.id,
        user.id,
    )

# -------------------------------------------------
# DELETE CHAT
# -------------------------------------------------
@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_chat(
    db: AsyncSession = Depends(get_db),
    chat = Depends(get_owned_chat),
    chats: ChatRepository = Depends(
        get_chat_repository
    ),
):
    await chats.delete(
        db,
        chat,
    )
    return {
        "message": "Chat deleted",
    }