from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import get_owned_workflow_run, get_workflow_event_repository
from app.models import WorkflowRun
from app.repositories import (
    WorkflowEventRepository,
)
from app.schemas import WorkflowEventResponse

router = APIRouter()

# -------------------------------------------------
#  GET WORKFLOW EVENTS
# -------------------------------------------------
@router.get(
    "/workflow_runs/{run_id}/events",
    response_model=list[WorkflowEventResponse],
)
async def get_workflow_events(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun =Depends(get_owned_workflow_run),
    events: WorkflowEventRepository = Depends(
        get_workflow_event_repository
    ),
):

    return await events.get_for_user_run(
        db=db,
        run_id=workflow_run.id,
    )

# 10,000+ events
# will become expensive.

# Future:
# GET /workflow_runs/{run_id}/events?limit=100&offset=0