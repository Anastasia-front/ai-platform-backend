from datetime import datetime

from pydantic import BaseModel

from app.enums import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    created_at: datetime

    class Config:
        from_attributes = True