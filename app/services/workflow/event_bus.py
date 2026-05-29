import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkflowRunEvent


class EventBus:

    async def emit(
        self,
        db: AsyncSession,
        workflow_run_id: int,
        event_type: str,
        data: dict,
    ) -> str:

        db.add(
            WorkflowRunEvent(
                workflow_run_id=workflow_run_id,
                event_type=event_type,
                payload=data,
            )
        )

        await db.flush()

        return (
            f"event: {event_type}\n"
            f"data: {json.dumps(data)}\n\n"
        )