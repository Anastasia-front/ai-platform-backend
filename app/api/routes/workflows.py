from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, status

from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
)

router = APIRouter()


@router.get(
    "/projects/{project_id}/workflows",
    response_model=List[WorkflowResponse],
)
async def get_workflows(
    project_id: int,
):
    return [
        {
            "id": 1,
            "project_id": project_id,
            "name": "Research Workflow",
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
        }
    ]


@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    project_id: int,
    payload: WorkflowCreate,
):
    return {
        "id": 1,
        "project_id": project_id,
        "name": payload.name,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }