
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_owned_workflow_run,
    get_workflow_service,
)
from app.schemas import WorkflowRunResponse
from app.services import WorkflowService

router = APIRouter()

# -------------------------------------------------
#  GET SINGLE WORKFLOW RUN
# -------------------------------------------------
@router.get(
    "/workflow_runs/{run_id}",
    response_model=WorkflowRunResponse,
)
async def get_workflow_run(
    workflow_run=Depends(get_owned_workflow_run),
):
    return workflow_run

# -------------------------------------------------
#  RESUME WORKFLOW RUN
# -------------------------------------------------
@router.post(
    ("/workflow_runs/{run_id}/resume"),
    response_model=WorkflowRunResponse,
)
async def resume_workflow(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    workflow_run=Depends(get_owned_workflow_run),
    service: WorkflowService = Depends(get_workflow_service),
):
    output = await service.resume_workflow(
        db=db,
        run_id=run_id,
    )

    return WorkflowRunResponse(
    workflow_id=workflow_run.workflow_id,
    input=workflow_run.input,
    output=output,
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