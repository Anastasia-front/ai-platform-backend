from datetime import datetime

from pydantic import BaseModel


class WorkflowStepRunResponse(BaseModel):
    id: int
    workflow_run_id: int
    workflow_step_id: int
    input: str
    output: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True