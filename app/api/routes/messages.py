from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, status

from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)

router = APIRouter()


@router.get(
    "/chats/{chat_id}/messages",
    response_model=List[MessageResponse],
)
async def get_messages(
    chat_id: int,
):
    return [
        {
            "id": 1,
            "chat_session_id": chat_id,
            "role": "assistant",
            "content": "Hello",
            "created_at": datetime.now(timezone.utc),
        }
    ]


@router.post(
    "/chats/{chat_id}/messages",
    response_model=List[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    chat_id: int,
    payload: MessageCreate,
):
    user_message = {
        "id": 1,
        "chat_session_id": chat_id,
        "role": "user",
        "content": payload.content,
        "created_at": datetime.now(timezone.utc),
    }

    assistant_message = {
        "id": 2,
        "chat_session_id": chat_id,
        "role": "assistant",
        "content": f"AI response to: {payload.content}",
        "created_at": datetime.now(timezone.utc),
    }

    return [
        user_message,
        assistant_message,
    ]