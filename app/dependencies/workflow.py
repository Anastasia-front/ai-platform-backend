from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories import (
    WorkflowRepository,
    WorkflowRunRepository,
)
from app.services.workflow.dag_engine import DAGEngine
from app.services.workflow.event_bus import EventBus
from app.services.workflow.workflow import WorkflowService

workflows = WorkflowRepository()


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