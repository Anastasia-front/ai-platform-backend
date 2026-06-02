from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflow.dag_engine import DAGEngine
from app.services.workflow.event_bus import EventBus

from ...repositories.workflow_runs import (
    WorkflowRunRepository,
)


class WorkflowService:

    def __init__(self):

        self.engine = DAGEngine()
        self.events = EventBus()
        self.runs = WorkflowRunRepository()

    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ) -> str:

        workflow_run = await self.runs.create(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

        output = await self.engine.execute(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )

        await self.runs.complete(
            db=db,
            workflow_run=workflow_run,
            output=output or "",
        )

        await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )

        await db.commit()

        return output or ""

    async def run_workflow_stream(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):

        workflow_run = await self.runs.create(
            db=db,
            workflow_id=workflow_id,
            user_input=user_input,
        )

        output = await self.engine.execute(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )

        await self.runs.complete(
            db=db,
            workflow_run=workflow_run,
            output=output or "",
        )

        yield await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )

        await db.commit()