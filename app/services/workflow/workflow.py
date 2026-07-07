from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    WorkflowRunRepository,
)
from app.services.workflow import DAGEngine, EventBus


class WorkflowService:

    def __init__(
        self,
        runs: WorkflowRunRepository,
        events: EventBus,
        engine: DAGEngine,
    ):
        self.runs = runs
        self.events = events
        self.engine = engine

    async def run_workflow(
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

        await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )

        await db.commit()

        await db.refresh(workflow_run)
        return workflow_run

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


# business logic
# load run
# call DAG engine
# resume execution
    async def resume_workflow(
        self,
        db: AsyncSession,
        run_id: int,
    ):

        workflow_run = await self.runs.get_by_id(
            db,
            run_id,
        )

        if not workflow_run:
            raise ValueError("Workflow run not found")

        output = await self.engine.execute(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_run.workflow_id,
            user_input=workflow_run.input,
            max_retries=3,
            continue_on_error=True,
        )

        return output
