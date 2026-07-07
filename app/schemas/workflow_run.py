from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowRunRequest(BaseModel):
    input: str


class WorkflowRunResponse(BaseModel):
    id: int
    workflow_id: int
    input: str
    output: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
