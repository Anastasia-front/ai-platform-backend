from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Project, Workflow, WorkflowStep


class WorkflowStepRepository:

    async def create(self, db: AsyncSession, step: WorkflowStep):
        db.add(step)
        await db.flush()

        return step

    async def get_by_id(
        self,
        db: AsyncSession,
        step_id: int,
    ):
        result = await db.execute(
            select(WorkflowStep)
            .join(Workflow)
            .join(Project)
            .where(
                WorkflowStep.id == step_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        db: AsyncSession,
        step_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(WorkflowStep)
            .join(
                Workflow,
                Workflow.id == WorkflowStep.workflow_id,
            )
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                WorkflowStep.id == step_id,
                Project.user_id == user_id,
            )
            .options(selectinload(WorkflowStep.workflow).selectinload(Workflow.project))
        )

        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
    ):
        result = await db.execute(
            select(WorkflowStep)
            .join(
                Workflow,
                Workflow.id == WorkflowStep.workflow_id,
            )
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                Project.user_id == user_id,
            )
            .order_by(
                WorkflowStep.step_order,
            )
        )

        return result.scalars().all()

    async def list_for_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
    ):

        result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        step: WorkflowStep,
    ):
        await db.delete(step)

        await db.flush()
