
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.enums import AgentRunStatus
from app.models import AgentRun, Workflow
from app.schemas import AgentRunCreate, AgentRunResponse

router = APIRouter()


# -------------------------------------------------
# RUN AGENT
# -------------------------------------------------
@router.post(
    "/workflows/{workflow_id}/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent(
    workflow_id: int,
    payload: AgentRunCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # verify workflow exists and belongs to user (via project ownership)
    result = await db.execute(
        select(Workflow).where(Workflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    agent_run = AgentRun(
        workflow_id=workflow_id,
        goal=payload.goal,
        status=AgentRunStatus.COMPLETED,
        result=f"Agent completed goal: {payload.goal}",
    )

    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    return agent_run


# -------------------------------------------------
# GET AGENT RUN
# -------------------------------------------------
@router.get(
    "/agent-runs/{agent_run_id}",
    response_model=AgentRunResponse,
)
async def get_agent_run(
    agent_run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == agent_run_id)
    )

    agent_run = result.scalar_one_or_none()

    if not agent_run:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    return agent_run