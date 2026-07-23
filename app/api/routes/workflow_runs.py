from math import ceil

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_background_job_service,
    get_current_user,
    get_owned_workflow_run,
    get_workflow_event_repository,
    get_workflow_run_repository,
    get_workflow_service,
)
from app.enums import WorkflowRunStatus
from app.models import User, WorkflowRun
from app.repositories import (
    WorkflowEventRepository,
    WorkflowRunRepository,
)
from app.schemas import (
    WorkflowEventResponse,
    WorkflowRunBulkDeleteResponse,
    WorkflowRunListResponse,
    WorkflowRunResponse,
)
from app.services import BackgroundJobService, WorkflowService

router = APIRouter()


# -------------------------------------------------
#  LIST WORKFLOW RUNS
# -------------------------------------------------
@router.get(
    "/runs",
    response_model=WorkflowRunListResponse,
)
async def list_workflow_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: WorkflowRunStatus | None = Query(None, alias="status"),
    project_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    runs: WorkflowRunRepository = Depends(get_workflow_run_repository),
):
    total = await runs.count_for_user(
        db=db,
        user_id=user.id,
        status=status_filter,
        project_id=project_id,
    )
    items = await runs.list_for_user(
        db=db,
        user_id=user.id,
        status=status_filter,
        project_id=project_id,
        limit=page_size,
        offset=(page - 1) * page_size,
    )

    return WorkflowRunListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )

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
    status_code=status.HTTP_202_ACCEPTED,
)
async def resume_workflow(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    workflow_run = await service.enqueue_resume(db, workflow_run, jobs)

    return service.run_response(workflow_run)


# -------------------------------------------------
#  RETRY WORKFLOW RUN
# -------------------------------------------------
@router.post(
    "/runs/{run_id}/retry",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_workflow(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    workflow_run = await service.enqueue_retry(db, workflow_run, jobs)

    return service.run_response(workflow_run)

# -------------------------------------------------
#  CANCEL WORKFLOW RUN
# -------------------------------------------------
@router.post(
    "/runs/{run_id}/cancel",
    response_model=WorkflowRunResponse,
)
async def cancel_workflow_run(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    workflow_run = await service.cancel_run(db, workflow_run, jobs)
    return service.run_response(workflow_run)

# -------------------------------------------------
#  DELETE CANCELED WORKFLOW RUNS
# -------------------------------------------------
@router.delete(
    "/runs/canceled",
    response_model=WorkflowRunBulkDeleteResponse,
)
async def delete_canceled_workflow_runs(
    project_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
):
    deleted = await service.delete_canceled_runs(
        db=db,
        user_id=user.id,
        project_id=project_id,
    )
    return WorkflowRunBulkDeleteResponse(deleted=deleted)

# -------------------------------------------------
#  DELETE WORKFLOW RUN
# -------------------------------------------------
@router.delete(
    "/runs/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow_run(
    db: AsyncSession = Depends(get_db),
    workflow_run: WorkflowRun = Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
):
    await service.delete_run(db, workflow_run)
    return None


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
