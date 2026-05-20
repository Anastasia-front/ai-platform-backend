from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    filepath: str
    status: Literal[
        "uploaded",
        "processing",
        "indexed",
        "failed",
    ]
    created_at: datetime