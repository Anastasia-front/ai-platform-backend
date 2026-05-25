from datetime import datetime

from pydantic import BaseModel


class WorkflowRunRequest(BaseModel):
    input: str


class WorkflowRunResponse(BaseModel):
    workflow_id: int
    input: str
    output: str
    created_at: datetime