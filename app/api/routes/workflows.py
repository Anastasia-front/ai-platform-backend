from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.core import get_db
from app.dependencies import (
    get_owned_project,
    get_owned_workflow,
    get_workflow_repository,
    get_workflow_service,
)
from app.enums import WorkflowRunStatus
from app.models import Project, Workflow
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
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    workflows: WorkflowRepository = Depends(get_workflow_repository),
):
    workflow = Workflow(
        project_id=project.id,
        name=payload.name,
        status=WorkflowRunStatus.RUNNING,
    )

    await workflows.create(db, workflow)
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
    workflow: Workflow = Depends(get_owned_workflow),
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
    workflows: WorkflowRepository = Depends(get_workflow_repository),
):
    await workflows.delete(db, workflow)
    await db.commit()


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
    service: WorkflowService = Depends(
        get_workflow_service,
    ),
    workflow: Workflow = Depends(get_owned_workflow),
):
    workflow_run = await service.run_workflow(
        db=db,
        workflow_id=workflow.id,
        user_input=payload.input,
    )

    return WorkflowRunResponse(
        id=workflow_run.id,
        workflow_id=workflow.id,
        input=payload.input,
        output=workflow_run.output,
        status=workflow_run.status,
        created_at=workflow_run.created_at,
    )


# -------------------------------------------------
# STREAMING ROUTE
# -------------------------------------------------
@router.post("/workflows/{workflow_id}/runs/stream")
async def run_workflow_stream(
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    service: WorkflowService = Depends(get_workflow_service),
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
