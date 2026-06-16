from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project


class ProjectRepository:

    async def create(
        self,
        db: AsyncSession,
        project: Project,
        user_id:int,
    ):
        project.user_id = user_id
        db.add(project)
        await db.flush()

        return project

    async def get_by_id(
        self,
        db: AsyncSession,
        project_id: int,
    ):
        result = await db.execute(
            select(Project).where(
                Project.id == project_id
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
    ):
        result = await db.execute(
            select(Project)
            .where(
                Project.user_id == user_id
            )
            .order_by(Project.id.desc())
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        project: Project,
    ):
        await db.delete(project)

        await db.flush()