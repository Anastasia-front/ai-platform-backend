from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRunEvent


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