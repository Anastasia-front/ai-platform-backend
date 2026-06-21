from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import WorkflowRunStatus


class WorkflowCreate(BaseModel):
    name: str


class WorkflowResponse(BaseModel):
    id: int
    project_id: int
    name: str
    status: WorkflowRunStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)