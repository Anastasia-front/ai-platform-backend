from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime