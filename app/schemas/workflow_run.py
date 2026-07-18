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
    celery_task_id: str | None = None
    error: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunListResponse(BaseModel):
    items: list[WorkflowRunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WorkflowRunBulkDeleteResponse(BaseModel):
    deleted: int
