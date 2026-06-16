from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.repositories import get_chat_repository
from app.models import User
from app.repositories import ChatRepository


async def get_owned_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(
        get_chat_repository   )
):
    chat = await chats.get_for_user(
        db,
        chat_id,
        user.id,
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return chat