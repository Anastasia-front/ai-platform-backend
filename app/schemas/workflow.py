from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class WorkflowCreate(BaseModel):
    name: str


class WorkflowResponse(BaseModel):
    id: int
    project_id: int
    name: str
    status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
    ]
    created_at: datetime