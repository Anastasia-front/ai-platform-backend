from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.repositories import (
    WorkflowEventRepository,
    WorkflowRunRepository,
)
from app.schemas import WorkflowEventResponse

router = APIRouter()

events = WorkflowEventRepository()
runs = WorkflowRunRepository()

@router.get(
    "/workflow_runs/{run_id}/events",
    response_model=list[WorkflowEventResponse],
)
async def get_workflow_events(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    
    run = await runs.get_by_id(db, run_id)

    if not run:
        raise HTTPException(
            status_code=404,
            detail="Workflow run not found",
        )

    return await events.get_for_run(
        db,
        run_id,
    )

# 10,000+ events
# will become expensive.

# Future:
# GET /workflow_runs/{run_id}/events?limit=100&offset=0