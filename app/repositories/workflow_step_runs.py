from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
from app.models import WorkflowStepRun


class WorkflowStepRunRepository:

    async def create(
        self,
        db: AsyncSession,
        workflow_run_id: int,
        workflow_step_id: int,
        step_order: int,
        input: str,
        output: str | None,
        status: WorkflowRunStatus,
        execution_time_ms: int,
        retry_count: int = 0,
        error_message: str | None = None,
    ) -> WorkflowStepRun:
        run = WorkflowStepRun(
            workflow_run_id=workflow_run_id,
            workflow_step_id=workflow_step_id,
            step_order=step_order,
            input=input,
            output=output,
            status=status,
            execution_time_ms=execution_time_ms,
            retry_count=retry_count,
            error_message=error_message,
        )

        db.add(run)
        await db.flush()
        await db.refresh(run)

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