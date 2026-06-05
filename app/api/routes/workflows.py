from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.dependencies.workflow import get_workflow_service
from app.enums import WorkflowRunStatus
from app.models import Project, Workflow
from app.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from app.services import WorkflowService

router = APIRouter()


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
    user=Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await db.execute(
        select(Workflow).where(Workflow.project_id == project_id)
    )

    return result.scalars().all()


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
    user=Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id,
        )
    )

    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    workflow = Workflow(
        project_id=project_id,
        name=payload.name,
        status=WorkflowRunStatus.RUNNING,
    )

    db.add(workflow)
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
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )

    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    project_result = await db.execute(
        select(Project).where(Project.id == workflow.project_id)
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    return workflow


    # -------------------------------------------------
    # DELETE WORKFLOW
    # -------------------------------------------------
@router.delete(
    "/workflows/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )

    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    project_result = await db.execute(
        select(Project).where(Project.id == workflow.project_id)
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    await db.delete(workflow)
    await db.commit()

    return None



# -------------------------------------------------
# EXECUTION ROUTE
# -------------------------------------------------


@router.post(
    "/workflows/{workflow_id}/run",
    response_model=WorkflowRunResponse,
)
async def run_workflow(
    workflow_id: int,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    service: WorkflowService = Depends(
    get_workflow_service
)
):
    # 1. load workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )

    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    # 2. ownership check
    project_result = await db.execute(
        select(Project).where(Project.id == workflow.project_id)
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    # 3. execute workflow
    output = await service.run_workflow(
        db=db,
        workflow_id=workflow_id,
        user_input=payload.input,
    )

    # 4. response
    return WorkflowRunResponse(
        workflow_id=workflow_id,
        input=payload.input,
        output=output,
        created_at=datetime.now(timezone.utc),
    )

# -------------------------------------------------
# STREAMING ROUTE
# -------------------------------------------------

@router.post("/workflows/{workflow_id}/stream")
async def run_workflow_stream(
    workflow_id: int,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    async def event_generator():
        async for event in service.run_workflow_stream(
            db=db,
            workflow_id=workflow_id,
            user_input=payload.input,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
