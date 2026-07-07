from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_current_user,
    get_owned_workflow_run,
    get_workflow_event_repository,
    get_workflow_run_repository,
    get_workflow_service,
)
from app.models import User, WorkflowRun
from app.repositories import (
    WorkflowEventRepository,
    WorkflowRunRepository,
)
from app.schemas import WorkflowEventResponse, WorkflowRunResponse
from app.services import WorkflowService

router = APIRouter()


# -------------------------------------------------
#  LIST WORKFLOW RUNS
# -------------------------------------------------
@router.get(
    "/runs",
    response_model=list[WorkflowRunResponse],
)
async def list_workflow_runs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    runs: WorkflowRunRepository = Depends(get_workflow_run_repository),
):
    return await runs.list_for_user(db, user.id)

# -------------------------------------------------
#  GET SINGLE WORKFLOW RUN
# -------------------------------------------------
@router.get(
    "/runs/{run_id}",
    response_model=WorkflowRunResponse,
)
async def get_workflow_run(
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
):
    return workflow_run


# -------------------------------------------------
#  RESUME WORKFLOW RUN
# -------------------------------------------------
@router.post(
    ("/runs/{run_id}/resume"),
    response_model=WorkflowRunResponse,
)
async def resume_workflow(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
):
    output = await service.resume_workflow(
        db=db,
        run_id=run_id,
    )

    return WorkflowRunResponse(
        id=workflow_run.id,
        workflow_id=workflow_run.workflow_id,
        input=workflow_run.input,
        output=output,
        status=workflow_run.status,
        created_at=workflow_run.created_at,
    )


# add later:

# GET /workflow_runs

# with filters:

# GET /workflow_runs?workflow_id=1
# GET /workflow_runs?status=completed
# GET /workflow_runs?status=failed

# This becomes very useful once you have dozens of runs.

# A workflow engine almost always needs a "list runs" endpoint.


# -------------------------------------------------
#  GET WORKFLOW EVENTS
# -------------------------------------------------
@router.get(
    "/runs/{run_id}/events",
    response_model=list[WorkflowEventResponse],
)
async def get_workflow_events(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    events: WorkflowEventRepository = Depends(get_workflow_event_repository),
):

    return await events.get_for_run(
        db=db,
        run_id=workflow_run.id,
    )


# 10,000+ events
# will become expensive.

# Future:
# GET /workflow_runs/{run_id}/events?limit=100&offset=0
