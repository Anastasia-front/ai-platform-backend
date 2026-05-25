from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas import WorkflowRunRequest, WorkflowRunResponse
from app.services import WorkflowService

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

@router.post("/workflows/{workflow_id}/stream")
async def run_workflow_stream(
    workflow_id: int,
    payload: WorkflowRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    service = WorkflowService()

    async def event_generator():
        async for event in service.run_workflow_stream(
            db=db,
            workflow_id=workflow_id,
            user_input=payload.input,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )