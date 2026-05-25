from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Project, Workflow, WorkflowStep
from app.schemas import WorkflowStepCreate, WorkflowStepResponse

router = APIRouter()


# -------------------------------------------------
# GET WORKFLOW STEPS
# -------------------------------------------------
@router.get(
    "/workflows/{workflow_id}/steps",
    response_model=List[WorkflowStepResponse],
)
async def get_workflow_steps(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # --------------------------------
    # LOAD WORKFLOW
    # --------------------------------
    workflow_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id
        )
    )

    workflow = workflow_result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    # --------------------------------
    # VERIFY OWNERSHIP
    # --------------------------------
    project_result = await db.execute(
        select(Project).where(
            Project.id == workflow.project_id
        )
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    # --------------------------------
    # LOAD STEPS
    # --------------------------------
    result = await db.execute(
        select(WorkflowStep)
        .where(
            WorkflowStep.workflow_id == workflow_id
        )
        .order_by(WorkflowStep.step_order)
    )

    return result.scalars().all()


# -------------------------------------------------
# CREATE WORKFLOW STEP
# -------------------------------------------------
@router.post(
    "/workflows/{workflow_id}/steps",
    response_model=WorkflowStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_step(
    workflow_id: int,
    payload: WorkflowStepCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # --------------------------------
    # LOAD WORKFLOW
    # --------------------------------
    workflow_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id
        )
    )

    workflow = workflow_result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    # --------------------------------
    # VERIFY OWNERSHIP
    # --------------------------------
    project_result = await db.execute(
        select(Project).where(
            Project.id == workflow.project_id
        )
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    # --------------------------------
    # CREATE STEP
    # --------------------------------
    step = WorkflowStep(
        workflow_id=workflow_id,
        step_order=payload.step_order,
        name=payload.name,
        prompt_template=payload.prompt_template,
    )

    db.add(step)

    await db.commit()
    await db.refresh(step)

    return step


# -------------------------------------------------
# DELETE WORKFLOW STEP
# -------------------------------------------------
@router.delete(
    "/workflow-steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow_step(
    step_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # --------------------------------
    # LOAD STEP
    # --------------------------------
    result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.id == step_id
        )
    )

    step = result.scalar_one_or_none()

    if not step:
        raise HTTPException(
            status_code=404,
            detail="Workflow step not found",
        )

    # --------------------------------
    # LOAD WORKFLOW
    # --------------------------------
    workflow_result = await db.execute(
        select(Workflow).where(
            Workflow.id == step.workflow_id
        )
    )

    workflow = workflow_result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    # --------------------------------
    # VERIFY OWNERSHIP
    # --------------------------------
    project_result = await db.execute(
        select(Project).where(
            Project.id == workflow.project_id
        )
    )

    project = project_result.scalar_one_or_none()

    if not project or project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed",
        )

    # --------------------------------
    # DELETE STEP
    # --------------------------------
    await db.delete(step)

    await db.commit()

    return None