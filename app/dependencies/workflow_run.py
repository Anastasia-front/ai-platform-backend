from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_workflow_run_repository
from app.repositories import WorkflowRunRepository


async def get_owned_workflow_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    runs: WorkflowRunRepository = Depends(
        get_workflow_run_repository
    )
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