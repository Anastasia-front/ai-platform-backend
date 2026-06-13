from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories import WorkflowRunRepository

runs = WorkflowRunRepository()


async def get_owned_workflow_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    workflow_run = await runs.get_for_user(
        db=db,
        run_id=run_id,
        user_id=user.id,
    )

    if not workflow_run:
        raise HTTPException(
            status_code=404,
            detail="Workflow run not found",
        )

    return workflow_run