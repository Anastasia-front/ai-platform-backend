from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
from app.models import WorkflowRun


class WorkflowRunRepository:

    async def create(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
    ) -> WorkflowRun:

        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)

        await db.flush()

        return workflow_run

    async def complete(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
        output: str,
    ):

        workflow_run.output = output
        workflow_run.status = WorkflowRunStatus.COMPLETED

        await db.flush()

    async def fail(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
    ):

        workflow_run.status = WorkflowRunStatus.FAILED

        await db.flush()

    async def get_running(
        self,
        db: AsyncSession,
    ):
        result = await db.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.status == "running"
            )
        )

        return result.scalars().all()
    

    async def get_by_id(
        self,
        db: AsyncSession,
        run_id: int,
    ):
        result = await db.execute(
            select(WorkflowRun).where(
                WorkflowRun.id == run_id
            )
        )

        return result.scalar_one_or_none()