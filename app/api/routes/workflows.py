from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core import get_db
from app.dependencies import (
    get_owned_workflow,
    get_workflow_repository,
    get_workflow_service,
)
from app.enums import WorkflowRunStatus
from app.models import Workflow
from app.repositories import WorkflowRepository
from app.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from app.services import WorkflowService

router = APIRouter()

# -------------------------------------------------
# CREATE WORKFLOW
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    project_id: int,
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    workflows: WorkflowRepository = Depends(
        get_workflow_repository
    ),
):
    workflow = Workflow(
        project_id=project_id,
        name=payload.name,
        status=WorkflowRunStatus.RUNNING,
    )

    await workflows.create(
        db,
        workflow
    )
    await db.commit()
    await db.refresh(workflow)

    return workflow

# -------------------------------------------------
# GET SINGLE WORKFLOW
# -------------------------------------------------
@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
)
async def get_workflow(
    workflow=Depends(get_owned_workflow),
):
    return workflow

# -------------------------------------------------
# GET WORKFLOWS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/workflows",
    response_model=List[WorkflowResponse],
)
async def get_workflows(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await WorkflowRepository.list_for_project(
        db,
        project_id,
    )

# -------------------------------------------------
# DELETE WORKFLOW
# -------------------------------------------------
@router.delete(
    "/workflows/{workflow_id}",
    status_code=204,
)
async def delete_workflow(
    workflow = Depends(get_owned_workflow),
    workflows: WorkflowRepository = Depends(
        get_workflow_repository
    ),
):
    await workflows.delete(workflow)

    return None

# -------------------------------------------------
#  CREATE WORKFLOW RUN
# -------------------------------------------------
@router.post(
    "/workflows/{workflow_id}/run",
    response_model=WorkflowRunResponse,
)
async def run_workflow(
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    service: WorkflowService  = Depends(
        get_workflow_service,
    ),
    workflow=Depends(get_owned_workflow),
):
    output = await service.run_workflow(
        db=db,
        workflow_id=workflow.id,
        user_input=payload.input,
    )

    return WorkflowRunResponse(
        workflow_id=workflow.id,
        input=payload.input,
        output=output,
        created_at=datetime.now(datetime.timezone.utc),
    )   

# -------------------------------------------------
# STREAMING ROUTE
# -------------------------------------------------
@router.post("/workflows/{workflow_id}/runs/stream")
async def run_workflow_stream(
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    workflow=Depends(get_owned_workflow),
    service: WorkflowService  = Depends(get_workflow_service),
):
    async def event_generator():
        async for event in service.run_workflow_stream(
            db=db,
            workflow_id=workflow.id,
            user_input=payload.input,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )