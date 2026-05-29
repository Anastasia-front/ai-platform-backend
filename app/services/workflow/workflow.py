
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRun
from app.services.workflow.dag_engine import DAGEngine
from app.services.workflow.event_bus import EventBus


class WorkflowService:

    def __init__(self):
        self.engine = DAGEngine()
        self.events = EventBus()

    # =====================================================
    # NORMAL EXECUTION
    # =====================================================
    async def run_workflow(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ) -> str:

        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)

        await db.flush()

        output = await self.engine.execute(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )

        await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )

        return output or ""

    # =====================================================
    # STREAMING EXECUTION
    # =====================================================
    async def run_workflow_stream(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_input: str,
        max_retries: int = 3,
        continue_on_error: bool = True,
    ):

        workflow_run = WorkflowRun(
            workflow_id=workflow_id,
            input=user_input,
            status="running",
        )

        db.add(workflow_run)

        await db.flush()

        output = await self.engine.execute(
            db=db,
            workflow_run=workflow_run,
            workflow_id=workflow_id,
            user_input=user_input,
            max_retries=max_retries,
            continue_on_error=continue_on_error,
        )

        yield await self.events.emit(
            db,
            workflow_run.id,
            "workflow_done",
            {
                "output": output,
            },
        )