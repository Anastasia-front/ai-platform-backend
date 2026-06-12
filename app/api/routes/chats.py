from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import chats, projects
from app.core.database import get_db
from app.dependencies import get_current_user, get_owned_chat
from app.models import Chat, User
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
    project = await projects.get_for_user(
        db,
        project_id,
        user.id,
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    chats_result = await chats.get_for_user(
        db,
        project_id,
        user.id,
    )

    return chats_result


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
    project_result = await projects.get_for_user(
            db,
            project_id,
            user.id,
        )

    if not project_result:
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
    chat = Depends(get_owned_chat),
):
    return chat


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
):
    await chats.delete(
    db,
    chat,
)
    return {
        "message": "Chat deleted",
    }