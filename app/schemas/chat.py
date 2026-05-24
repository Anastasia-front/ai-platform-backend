from datetime import datetime

from pydantic import BaseModel


class ChatCreate(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: int
    project_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True