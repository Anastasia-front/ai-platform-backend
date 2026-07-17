from datetime import datetime, timezone

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
        include_deleted: bool = False,
    ):
        query = select(Workflow).where(Workflow.id == workflow_id)
        if not include_deleted:
            query = query.where(Workflow.deleted_at.is_(None))

        result = await db.execute(
            query
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_id: int,
        include_deleted: bool = False,
    ):
        query = (
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
        if not include_deleted:
            query = query.where(Workflow.deleted_at.is_(None))

        result = await db.execute(
            query
        )

        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        db: AsyncSession,
        project_id: int,
        include_deleted: bool = False,
    ):
        query = (
            select(Workflow)
            .where(
                Workflow.project_id == project_id
            )
            .order_by(Workflow.id.desc())
        )
        if not include_deleted:
            query = query.where(Workflow.deleted_at.is_(None))

        result = await db.execute(
            query
        )

        return result.scalars().all()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        include_deleted: bool = False,
    ):
        query = (
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
        if not include_deleted:
            query = query.where(Workflow.deleted_at.is_(None))

        result = await db.execute(
            query
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        workflow: Workflow,
    ):
        if workflow.deleted_at is None:
            workflow.deleted_at = datetime.now(timezone.utc)

        await db.flush()

    async def update_name(
        self,
        db: AsyncSession,
        workflow: Workflow,
        name: str,
    ):
        workflow.name = name
        await db.flush()
        await db.refresh(workflow)

        return workflow
