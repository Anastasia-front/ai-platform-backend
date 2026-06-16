from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
from app.models import WorkflowStepRun


class WorkflowStepRunRepository:

    async def create(
        self,
        db: AsyncSession,
        run: WorkflowStepRun
    ):
        db.add(run)
        await db.flush()

        return run
    
    async def list_completed_for_run(
        self,
        db: AsyncSession,
        workflow_run_id: int,
    ):
        result = await db.execute(
            select(WorkflowStepRun)
            .where(
                WorkflowStepRun.workflow_run_id
                == workflow_run_id,
                WorkflowStepRun.status
                == WorkflowRunStatus.COMPLETED,
            )
            .order_by(
                WorkflowStepRun.step_order
            )
        )

        return result.scalars().all()

    async def get_step_run(
        self,
        db: AsyncSession,
        workflow_run_id: int,
        workflow_step_id: int,
    ):
        result = await db.execute(
            select(WorkflowStepRun).where(
                WorkflowStepRun.workflow_run_id == workflow_run_id,
                WorkflowStepRun.workflow_step_id == workflow_step_id,
            )
        )

        return result.scalar_one_or_none()