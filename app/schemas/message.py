from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import AgentType, MessageRole


class MessageCreate(BaseModel):
    content: str
    agent_name: AgentType | None = None

class SourceMetadata(BaseModel):
    document_id: int
    document_name: str
    matches: int
    best_score: float

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    created_at: datetime
    sources: list[SourceMetadata] = []

    model_config = ConfigDict(from_attributes=True)
