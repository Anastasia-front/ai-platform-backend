from datetime import datetime

from pydantic import BaseModel

from app.enums import WorkflowRunStatus


class WorkflowCreate(BaseModel):
    name: str


class WorkflowResponse(BaseModel):
    id: int
    project_id: int
    name: str
    status: WorkflowRunStatus
    created_at: datetime

    class Config:
        from_attributes = True