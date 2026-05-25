from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chat, Message, Project, User
from app.schemas import MessageCreate


# -------------------------------------------------
# CREATE MESSAGE
# -------------------------------------------------
async def create_message(
    db: AsyncSession,
    chat_id: int,
    payload: MessageCreate,
    user: User,
) -> Message:

    # get chat
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )

    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    # verify ownership through project
    project_result = await db.execute(
        select(Project).where(
            Project.id == chat.project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    message = Message(
        chat_id=chat_id,
        role='user',
        content=payload.content,
    )

    db.add(message)

    await db.commit()
    await db.refresh(message)

    return message


# -------------------------------------------------
# GET CHAT MESSAGES
# -------------------------------------------------
async def get_chat_messages(
    db: AsyncSession,
    chat_id: int,
    user: User,
):

    # get chat
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )

    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    # verify ownership
    project_result = await db.execute(
        select(Project).where(
            Project.id == chat.project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    result = await db.execute(
        select(Message).where(
            Message.chat_id == chat_id
        )
    )

    return result.scalars().all()


# -------------------------------------------------
# DELETE MESSAGE
# -------------------------------------------------
async def delete_message(
    db: AsyncSession,
    message_id: int,
    user: User,
):

    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )

    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found",
        )

    # get chat
    chat_result = await db.execute(
        select(Chat).where(Chat.id == message.chat_id)
    )

    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    # verify ownership
    project_result = await db.execute(
        select(Project).where(
            Project.id == chat.project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    await db.delete(message)
    await db.commit()

    return {"detail": "Message deleted"}