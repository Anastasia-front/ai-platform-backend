from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_agent_run_repository,
    get_owned_agent_run,
    get_owned_workflow,
)
from app.enums import AgentRunStatus
from app.models import AgentRun, Workflow
from app.repositories import AgentRunRepository
from app.schemas import (
    AgentRunCreate,
    AgentRunResponse,
)

router = APIRouter()


# -------------------------------------------------
# GET SINGLE AGENT RUN
# -------------------------------------------------
@router.get(
    "/agent_runs/{agent_run_id}",
    response_model=AgentRunResponse,
)
async def get_agent_run(
    agent_run: AgentRun = Depends(get_owned_agent_run),
):
    return agent_run


# -------------------------------------------------
# CREATE RUN AGENT
# -------------------------------------------------
@router.post(
    "/agent_runs/",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent(
    payload: AgentRunCreate,
    db: AsyncSession = Depends(get_db),
    workflow: Workflow = Depends(get_owned_workflow),
    agent_runs: AgentRunRepository = Depends(get_agent_run_repository),
):
    agent_run = AgentRun(
        workflow_id=workflow.id,
        goal=payload.goal,
        status=AgentRunStatus.COMPLETED,
        result=f"Agent completed goal: {payload.goal}",
    )

    await agent_runs.create(db, agent_run)
    await db.commit()
    await db.refresh(agent_run)

    return agent_run