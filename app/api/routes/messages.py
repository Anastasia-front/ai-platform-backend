from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENTS
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Chat, Message, Project
from app.schemas import MessageCreate, MessageResponse
from app.services import AIService

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

    # --------------------------------
    # LOAD CHAT HISTORY
    # --------------------------------
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )

    history = result.scalars().all()

    ollama_messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in history
    ]

    agent = AGENTS.get(chat.agent_name)

    if not agent:
        raise HTTPException(
            status_code=400,
            detail="Invalid agent",
        )

    ai_response = await ai_service.generate_chat_response(
        messages=ollama_messages,
        system_prompt=agent.system_prompt,
    )

    assistant_msg = Message(        
        chat_id=chat_id,
        role="assistant",
        content=ai_response,
    )

    db.add(assistant_msg)

    await db.commit()

    await db.refresh(assistant_msg)

    return [user_msg, assistant_msg]


    # correct backend orchestration:
    
    # verify ownership
    #     ↓
    # save user message
    #     ↓
    # commit
    #     ↓
    # load history
    #     ↓
    # call AI
    #     ↓
    # save assistant message
    #     ↓
    # commit
    #     ↓
    # return both