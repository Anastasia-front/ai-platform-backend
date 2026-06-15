from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, get_workflow_repository
from app.repositories import (
    WorkflowRepository,
    WorkflowRunRepository,
)
from app.services import DAGEngine, EventBus, WorkflowService


def get_workflow_service():

    return WorkflowService(
        runs=WorkflowRunRepository(),
        events=EventBus(),
        engine=DAGEngine(),
    )


async def get_owned_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    workflows: WorkflowRepository = Depends(
        get_workflow_repository
    )
):
    workflow = await workflows.get_for_user(
        db,
        workflow_id,
        user.id,
    )

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    return workflow