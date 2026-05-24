from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.project import Project
from app.models.user import User
from app.schemas.chat import ChatCreate


async def create_chat(
    db: AsyncSession,
    project_id: int,
    payload: ChatCreate,
    user: User,
) -> Chat:
    # verify project ownership
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    project = result.scalar_one_or_none()

    if not project:
        return None

    chat = Chat(
        project_id=project_id,
        title=payload.title,
        agent_name=payload.agent_name,
    )

    db.add(chat)

    await db.commit()
    await db.refresh(chat)

    return chat


async def get_project_chats(
    db: AsyncSession,
    project_id: int,
    user: User,
):
    result = await db.execute(
        select(Chat)
        .join(Project)
        .where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    return result.scalars().all()


async def get_chat_by_id(
    db: AsyncSession,
    chat_id: int,
    user: User,
):
    result = await db.execute(
        select(Chat)
        .join(Project)
        .where(
            Chat.id == chat_id,
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()


async def delete_chat(
    db: AsyncSession,
    chat: Chat,
):
    await db.delete(chat)
    await db.commit()