from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowEventResponse(BaseModel):
    id: int
    workflow_run_id: int
    event_type: str
    payload: dict
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )