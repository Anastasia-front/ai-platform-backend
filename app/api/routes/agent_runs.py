from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.schemas.agent_run import (
    AgentRunCreate,
    AgentRunResponse,
)

router = APIRouter()


@router.post(
    "/workflows/{workflow_id}/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_agent(
    workflow_id: int,
    payload: AgentRunCreate,
):
    return {
        "id": 1,
        "workflow_id": workflow_id,
        "goal": payload.goal,
        "status": "completed",
        "result": f"Agent completed goal: {payload.goal}",
        "created_at": datetime.now(timezone.utc),
    }


@router.get(
    "/agent-runs/{agent_run_id}",
    response_model=AgentRunResponse,
)
async def get_agent_run(
    agent_run_id: int,
):
    return {
        "id": agent_run_id,
        "workflow_id": 1,
        "goal": "Analyze documents",
        "status": "completed",
        "result": "Analysis completed successfully",
        "created_at": datetime.now(timezone.utc),
    }