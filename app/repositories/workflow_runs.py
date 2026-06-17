from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import WorkflowRunStatus
from app.models import Project, Workflow, WorkflowRun


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
            status= WorkflowRunStatus.RUNNING,
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
                WorkflowRun.status ==  WorkflowRunStatus.RUNNING
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
    
    async def get_for_user(
        self,
        db: AsyncSession,
        run_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(WorkflowRun)
            .join(
                Workflow,
                Workflow.id == WorkflowRun.workflow_id,
            )
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                WorkflowRun.id == run_id,
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
            select(WorkflowRun)
            .join(
                Workflow,
                Workflow.id == WorkflowRun.workflow_id,
            )
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                Project.user_id == user_id,
            )
            .order_by(WorkflowRun.created_at.desc())
        )

        return result.scalars().all()
    
    async def get_for_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(WorkflowRun)
            .join(
                Workflow,
                Workflow.id == WorkflowRun.workflow_id,
            )
            .join(
                Project,
                Project.id == Workflow.project_id,
            )
            .where(
                WorkflowRun.workflow_id == workflow_id,
                Project.user_id == user_id,
            )
            .order_by(WorkflowRun.created_at.desc())
        )

        return result.scalars().all()