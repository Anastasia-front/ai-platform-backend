from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums import WorkflowRunStatus


class WorkflowCreate(BaseModel):
    name: str


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkflowResponse(BaseModel):
    id: int
    project_id: int
    name: str
    status: WorkflowRunStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
