from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, status

from app.schemas.chat import (
    ChatCreate,
    ChatResponse,
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/chats",
    response_model=List[ChatResponse],
)
async def get_project_chats(
    project_id: int,
):
    return [
        {
            "id": 1,
            "project_id": project_id,
            "title": "Support Chat",
            "created_at": datetime.now(timezone.utc),
        }
    ]


@router.post(
    "/projects/{project_id}/chats",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat(
    project_id: int,
    payload: ChatCreate,
):
    return {
        "id": 1,
        "project_id": project_id,
        "title": payload.title,
        "created_at": datetime.now(timezone.utc),
    }

@router.get(
    "/chats/{chat_id}",
    response_model=ChatResponse,
)
async def get_chat(
    chat_id: int,
):
    return {
        "id": chat_id,
        "project_id": 1,
        "title": "Support Chat",
        "created_at": datetime.now(timezone.utc),
    }