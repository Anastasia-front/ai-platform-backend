from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.project import Project
from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
)

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
        status="pending",
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