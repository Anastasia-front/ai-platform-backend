from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel

from app.enums import AgentRunStatus


class AgentRunCreate(BaseModel):
    goal: str


class AgentRunResponse(BaseModel):
    id: int
    workflow_id: int
    goal: str
    status: AgentRunStatus
    result: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)