from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import chats
from app.core.database import get_db
from app.dependencies.auth import get_current_user


async def get_owned_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
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