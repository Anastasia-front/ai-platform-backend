from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Workflow


class WorkflowRepository:

    async def create(
        self,
        db: AsyncSession,
        workflow: Workflow
    ):
        db.add(workflow)
        await db.flush()

        return workflow

    async def get_by_id(
        self,
        db: AsyncSession,
        workflow_id: int,
    ):
        result = await db.execute(
            select(Workflow).where(
                Workflow.id == workflow_id
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(Workflow)
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                Workflow.id == workflow_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        db: AsyncSession,
        project_id: int,
    ):
        result = await db.execute(
            select(Workflow)
            .where(
                Workflow.project_id == project_id
            )
            .order_by(Workflow.id.desc())
        )

        return result.scalars().all()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
    ):
        result = await db.execute(
            select(Workflow)
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                Project.user_id == user_id
            )
            .order_by(Workflow.id.desc())
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        workflow: Workflow,
    ):
        await db.delete(workflow)

        await db.flush()