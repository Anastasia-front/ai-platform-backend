from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.workflow_run import WorkflowRunRequest, WorkflowRunResponse
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post(
    "/workflows/{workflow_id}/run",
    response_model=WorkflowRunResponse,
)
async def run_workflow(
    workflow_id: int,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkflowService()

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