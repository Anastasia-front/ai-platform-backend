from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core import get_db
from app.dependencies import (
    get_chat_service,
    get_current_user,
    get_message_repository,
    get_owned_chat,
)
from app.models import Chat, User
from app.repositories import MessageRepository
from app.schemas import (
    MessageCreate,
    MessageResponse,
)
from app.services import ChatService

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
        get_message_repository,
    ),
):
    return await messages.list_for_chat(
        db,
        chat.id,
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
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    chat: Chat = Depends(get_owned_chat),
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    user_msg, assistant_msg = await chat_service.create_message(
        db=db,
        chat=chat,
        user=user,
        content=payload.content,
        agent_name=payload.agent_name,
    )

    return [user_msg, assistant_msg]

# -------------------------------------------------
# STREAM MESSAGE
# -------------------------------------------------
@router.post(
    "/{chat_id}/messages/stream",
)
async def create_message_stream(
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    chat: Chat = Depends(get_owned_chat),
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return StreamingResponse(
        chat_service.create_message_stream(
            db=db,
            chat=chat,
            user=user,
            content=payload.content,
            agent_name=payload.agent_name,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

# -------------------------------------------------
# REGENERATE MESSAGE
# -------------------------------------------------
@router.post(
    "/messages/{message_id}/regenerate",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.regenerate_message(
        db=db,
        message_id=message_id,
        user=user,
    )
