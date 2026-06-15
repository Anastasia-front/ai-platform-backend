from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    WorkflowStep,
)


class WorkflowStepRepository:

    async def create(
        self,
        db: AsyncSession,
        **data,
    ):
        step = WorkflowStep(**data)

        db.add(step)

        await db.flush()

        return step

    async def get_by_id(
        self,
        db: AsyncSession,
        step_id: int,
    ):
        result = await db.execute(
            select(WorkflowStep).where(
                WorkflowStep.id == step_id
            )
        )

        return result.scalar_one_or_none()


    async def list_for_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
    ):

        result = await db.execute(
            select(WorkflowStep)
            .where(
                WorkflowStep.workflow_id
                == workflow_id
            )
            .order_by(
                WorkflowStep.step_order
            )
        )

        return result.scalars().all()
    
    async def delete(
        self,
        db: AsyncSession,
        step: WorkflowStep,
    ):
        await db.delete(step)

        await db.flush()