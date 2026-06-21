from datetime import datetime

from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)