from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.chat import Chat
from app.models.message import Message
from app.models.project import Project
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)
from app.services.ai import AIService

router = APIRouter()


# -------------------------------------------------
# GET MESSAGES
# -------------------------------------------------
@router.get(
    "/chats/{chat_id}/messages",
    response_model=List[MessageResponse],
)
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # verify chat ownership
    chat_result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )

    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    project_result = await db.execute(
        select(Project).where(Project.id == chat.project_id)
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )

    return result.scalars().all()


# -------------------------------------------------
# CREATE MESSAGE
# -------------------------------------------------
@router.post(
    "/chats/{chat_id}/messages",
    response_model=List[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    chat_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # verify chat ownership
    chat_result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )

    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    project_result = await db.execute(
        select(Project).where(Project.id == chat.project_id)
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    # ---------------------------
    # USER MESSAGE
    # ---------------------------
    user_msg = Message(
        chat_id=chat_id,
        role="user",
        content=payload.content,
    )

    db.add(user_msg)

    await db.flush()

    # ---------------------------
    # AI MESSAGE
    # ---------------------------

    ai_service = AIService()

    ai_response = await ai_service.generate_response(
        payload.content
    )
    assistant_msg = Message(        
        chat_id=chat_id,
        role="assistant",
        content=ai_response,
    )

    db.add(assistant_msg)

    await db.commit()

    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    return [user_msg, assistant_msg]