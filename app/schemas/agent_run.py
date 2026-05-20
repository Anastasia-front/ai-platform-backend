from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel


class AgentRunCreate(BaseModel):
    goal: str


class AgentRunResponse(BaseModel):
    id: int
    workflow_id: int
    goal: str
    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
    ]
    result: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)