from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import MessageRole


class MessageCreate(BaseModel):
    content: str

class SourceMetadata(BaseModel):
    document_id: int
    document_name: str
    chunk_id: int
    chunk_index: int
    score: float

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    created_at: datetime
    sources: list[SourceMetadata] = []

    model_config = ConfigDict(from_attributes=True)