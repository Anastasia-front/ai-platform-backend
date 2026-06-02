import json

from ...repositories.workflow_events import (
    WorkflowEventRepository,
)


class EventBus:

    def __init__(self):
        self.repo = WorkflowEventRepository()

    async def emit(
        self,
        db,
        workflow_run_id,
        event_type,
        payload,
    ):

        await self.repo.create(
            db=db,
            workflow_run_id=workflow_run_id,
            event_type=event_type,
            payload=payload,
        )

        return (
            f"event: {event_type}\n"
            f"data: {json.dumps(payload)}\n\n"
        )