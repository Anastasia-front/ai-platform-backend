from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_owned_workflow
from app.repositories import WorkflowStepRepository

steps = WorkflowStepRepository()

async def get_owned_workflow_step(
    step_id: int,
    workflow=Depends(get_owned_workflow),
    db: AsyncSession = Depends(get_db),
):
    step = await steps.get_by_id(db, step_id)

    if not step or step.workflow_id != workflow.id:
        raise HTTPException(
            status_code=404,
            detail="Workflow step not found",
        )

    return step