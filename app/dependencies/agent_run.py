from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.dependencies.repositories import (
    get_agent_run_repository,
)
from app.repositories import AgentRunRepository


async def get_owned_agent_run(
    agent_run_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    runs: AgentRunRepository = Depends(
        get_agent_run_repository,
    ),
):
    agent_run = await runs.get_for_user(
        db,
        agent_run_id,
        user.id,
    )

    if not agent_run:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    return agent_run