from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_owned_workflow,
    get_owned_workflow_step,
    get_workflow_step_repository,
)
from app.models import Workflow, WorkflowStep
from app.repositories import WorkflowStepRepository
from app.schemas import WorkflowStepCreate, WorkflowStepResponse

router = APIRouter()

# -------------------------------------------------
# CREATE WORKFLOW STEP
# -------------------------------------------------
@router.post(
    "/workflows/{workflow_id}/steps",
    response_model=WorkflowStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_step(
    payload: WorkflowStepCreate,
    db: AsyncSession = Depends(get_db),
    workflow: Workflow= Depends(get_owned_workflow),
    steps: WorkflowStepRepository = Depends(
        get_workflow_step_repository
    ),
):

    step = WorkflowStep(
        workflow_id=workflow.id,
        step_order=payload.step_order,
        name=payload.name,
        prompt_template=payload.prompt_template,
        depends_on=payload.depends_on,
        condition=payload.condition,
    )

    await steps.create(db, step)
    await db.commit()
    await db.refresh(step)

    return step

# -------------------------------------------------
#  GET SINGLE WORKFLOW STEP
# -------------------------------------------------
@router.get(
    "/steps/{step_id}", 
    response_model=WorkflowStepResponse
)
async def get_step(
    step: WorkflowStep = Depends(get_owned_workflow_step),
):
    return step

# -------------------------------------------------
# GET WORKFLOW STEPS
# -------------------------------------------------
@router.get(
    "/workflows/{workflow_id}/steps",
    response_model=List[WorkflowStepResponse],
)
async def list_for_workflow(
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    steps: WorkflowStepRepository = Depends(
        get_workflow_step_repository
    ),
):
    return await steps.list_for_workflow(
        db, 
        workflow.id,
    )

# -------------------------------------------------
# DELETE WORKFLOW STEP
# -------------------------------------------------
@router.delete(
    "/steps/{step_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_step(
    db: AsyncSession = Depends(get_db),
    step: WorkflowStep = Depends(get_owned_workflow_step),
    steps: WorkflowStepRepository = Depends(
        get_workflow_step_repository
    ),
):
    await steps.delete(db, step)
    await db.commit()