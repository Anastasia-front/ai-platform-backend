from datetime import datetime

from pydantic import BaseModel


class WorkflowRunRequest(BaseModel):
    input: str


class WorkflowRunResponse(BaseModel):
    workflow_id: int
    input: str
    output: str | None
    created_at: datetime