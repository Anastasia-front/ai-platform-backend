from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core import get_db
from app.dependencies import (
    get_background_job_service,
    get_owned_project,
    get_owned_workflow,
    get_workflow_repository,
    get_workflow_service,
    get_workflow_update_service,
)
from app.models import Project, Workflow
from app.repositories import WorkflowRepository
from app.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from app.services import BackgroundJobService, WorkflowService, WorkflowUpdateService

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
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    service: WorkflowUpdateService = Depends(get_workflow_update_service),
):
    return await service.create(db=db, payload=payload, project=project)


# -------------------------------------------------
# GET SINGLE WORKFLOW
# -------------------------------------------------
@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
)
async def get_workflow(
    workflow: Workflow = Depends(get_owned_workflow),
):
    return workflow


# -------------------------------------------------
# UPDATE WORKFLOW
# -------------------------------------------------
@router.patch(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
)
async def update_workflow(
    payload: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    service: WorkflowUpdateService = Depends(get_workflow_update_service),
):
    return await service.update(
        db=db,
        workflow=workflow,
        payload=payload,
    )


# -------------------------------------------------
# GET WORKFLOWS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/workflows",
    response_model=List[WorkflowResponse],
)
async def get_workflows(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    workflows: WorkflowRepository = Depends(get_workflow_repository),
):
    return await workflows.list_for_project(
        db,
        project.id,
    )


# -------------------------------------------------
# DELETE WORKFLOW
# -------------------------------------------------
@router.delete(
    "/workflows/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow(
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    service: WorkflowUpdateService = Depends(get_workflow_update_service),
):
    await service.delete(db, workflow)


# -------------------------------------------------
#  CREATE WORKFLOW RUN
# -------------------------------------------------
@router.post(
    "/workflows/{workflow_id}/run",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_workflow(
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
    workflow: Workflow = Depends(get_owned_workflow),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    workflow_run = await service.enqueue_run(
        db=db,
        workflow_id=workflow.id,
        user_input=payload.input,
        jobs=jobs,
    )

    return service.run_response(workflow_run)


# -------------------------------------------------
# STREAMING ROUTE
# -------------------------------------------------
@router.post("/workflows/{workflow_id}/runs/stream")
async def run_workflow_stream(
    request: Request,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    service: WorkflowService = Depends(get_workflow_service),
):
    return StreamingResponse(
        service.run_workflow_stream_until_disconnected(
            db=db,
            workflow_id=workflow.id,
            user_input=payload.input,
            is_disconnected=request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
