from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_workflow_service
from app.models import workflow_run
from app.repositories import WorkflowRunRepository
from app.schemas import WorkflowRunRequest, WorkflowRunResponse
from app.services import WorkflowService

router = APIRouter()


runs = WorkflowRunRepository()


@router.get(
    "/workflow_runs/{run_id}",
    response_model=WorkflowRunResponse,
)
async def get_workflow_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    workflow_run = await runs.get_by_id(
        db,
        run_id,
    )

    if not workflow_run:
        raise HTTPException(
            status_code=404,
            detail="Workflow run not found",
        )

    return workflow_run


@router.post(
    "/workflow_runs/{workflow_id}/run",
    response_model=WorkflowRunResponse,
)
async def run_workflow(
    workflow_id: int,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    service: WorkflowService = Depends(
        get_workflow_service
    ),
):

    output = await service.run_workflow(
        db=db,
        workflow_id=workflow_id,
        user_input=payload.input,
    )

    return WorkflowRunResponse(
        workflow_id=workflow_id,
        input=payload.input,
        output=output,
        created_at=None,  # optional improvement later
    )



@router.post(
    ("/workflow_runs/{run_id}/resume"),
    response_model=WorkflowRunResponse,
)
async def resume_workflow(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
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