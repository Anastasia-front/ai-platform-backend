from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    WorkflowStep,
)


class WorkflowStepRepository:

    async def get_workflow_steps(
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