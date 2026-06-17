from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENTS
from app.core import get_db
from app.dependencies import get_message_repository, get_owned_chat
from app.models import Chat, Message
from app.repositories import MessageRepository
from app.schemas import MessageCreate, MessageResponse
from app.services import AIService

router = APIRouter()

# -------------------------------------------------
# GET MESSAGES
# -------------------------------------------------
@router.get(
    "/{chat_id}/messages",
    response_model=List[MessageResponse],
)
async def get_messages(
    db: AsyncSession = Depends(get_db),
    chat: Chat = Depends(get_owned_chat),
    messages: MessageRepository = Depends(
        get_message_repository
    ),
):
    return await messages.list_for_chat(
        db,
        chat.id
    )

# -------------------------------------------------
# CREATE MESSAGE
# -------------------------------------------------
@router.post(
    "/{chat_id}/messages",
    response_model=List[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    chat_id: int,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    chat:Chat = Depends(get_owned_chat),
    messages: MessageRepository = Depends(
        get_message_repository
    ),
):

    # ---------------------------
    # USER MESSAGE
    # ---------------------------
    user_msg = Message(
        chat_id=chat_id,
        role="user",
        content=payload.content,
    )

    await messages.create(db, user_msg)

    await db.flush()

    # ---------------------------
    # AI MESSAGE
    # ---------------------------

    ai_service = AIService()

    history = await messages.list_for_chat(
        db,
        chat.id
    )


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

    await messages.create(db, assistant_msg)
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