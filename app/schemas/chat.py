from datetime import datetime

from pydantic import BaseModel

from app.enums import AgentType


class ChatCreate(BaseModel):
    title: str
    agent_name: AgentType = AgentType.ASSISTANT


class ChatResponse(BaseModel):
    id: int
    project_id: int
    title: str
    agent_name: AgentType
    created_at: datetime

    class Config:
        from_attributes = True