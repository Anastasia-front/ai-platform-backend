from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import Chat, Project, User
from app.schemas import ChatCreate, ChatResponse

router = APIRouter(
    tags=["Chats"],
)


# -------------------------------------------------
# GET PROJECT CHATS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/chats",
    response_model=List[ChatResponse],
)
async def get_project_chats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ensure project belongs to user
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await db.execute(
        select(Chat).where(Chat.project_id == project_id)
    )

    chats = result.scalars().all()

    return chats


# -------------------------------------------------
# CREATE CHAT
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    project_id: int,
    payload: ChatCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ensure project belongs to user
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    chat = Chat(
        project_id=project_id,
        title=payload.title,
        agent_name=payload.agent_name,
    )

    db.add(chat)

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
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat)
        .join(Project)
        .where(
            Chat.id == chat_id,
            Project.user_id == user.id,
        )
    )

    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return chat


# -------------------------------------------------
# DELETE CHAT
# -------------------------------------------------
@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Chat)
        .join(Project)
        .where(
            Chat.id == chat_id,
            Project.user_id == user.id,
        )
    )

    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    await db.delete(chat)
    await db.commit()

    return {
        "message": "Chat deleted",
    }