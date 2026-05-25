from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User
from app.schemas import ProjectCreate


async def create_project(
    db: AsyncSession,
    payload: ProjectCreate,
    user: User,
) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        user_id=user.id,
    )

    db.add(project)

    await db.commit()
    await db.refresh(project)

    return project


async def get_user_projects(
    db: AsyncSession,
    user: User,
):
    result = await db.execute(
        select(Project).where(Project.user_id == user.id)
    )

    return result.scalars().all()


async def get_project_by_id(
    db: AsyncSession,
    project_id: int,
    user: User,
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    return result.scalar_one_or_none()


async def delete_project(
    db: AsyncSession,
    project: Project,
):
    await db.delete(project)
    await db.commit()