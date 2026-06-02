from sqlalchemy.ext.asyncio import AsyncSession

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
        workflow_run.status = "completed"

        await db.flush()

    async def fail(
        self,
        db: AsyncSession,
        workflow_run: WorkflowRun,
    ):

        workflow_run.status = "failed"

        await db.flush()