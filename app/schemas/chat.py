from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChatCreate(BaseModel):
    title: str

    agent_name: Literal[
        "assistant",
        "coding",
        "research",
    ] = "assistant"


class ChatResponse(BaseModel):
    id: int
    project_id: int
    title: str
    agent_name: str
    created_at: datetime

    class Config:
        from_attributes = True