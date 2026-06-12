from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


class MessageRepository:

    async def create(
        self,
        db: AsyncSession,
        **data,
    ):
        message = Message(**data)

        db.add(message)

        await db.flush()

        return message

    async def get_by_id(
        self,
        db: AsyncSession,
        message_id: int,
    ):
        result = await db.execute(
            select(Message).where(
                Message.id == message_id
            )
        )

        return result.scalar_one_or_none()

    async def list_for_chat(
        self,
        db: AsyncSession,
        chat_id: int,
    ):
        result = await db.execute(
            select(Message)
            .where(
                Message.chat_id == chat_id
            )
            .order_by(Message.created_at)
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        message: Message,
    ):
        await db.delete(message)

        await db.flush()