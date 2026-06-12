from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRun, WorkflowRunEvent


class WorkflowEventRepository:

    async def create(
        self,
        db: AsyncSession,
        workflow_run_id: int,
        event_type: str,
        payload: dict,
    ):

        event = WorkflowRunEvent(
            workflow_run_id=workflow_run_id,
            event_type=event_type,
            payload=payload,
        )

        db.add(event)

        await db.flush()

        return event
    
    async def get_for_user_run(
        self,
        db: AsyncSession,
        run_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(WorkflowRunEvent)
            .join(
                WorkflowRun,
                WorkflowRun.id
                == WorkflowRunEvent.workflow_run_id,
            )
            .where(
                WorkflowRunEvent.workflow_run_id
                == run_id,
                WorkflowRun.user_id == user_id,
            )
            .order_by(WorkflowRunEvent.created_at)
        )

        return result.scalars().all()