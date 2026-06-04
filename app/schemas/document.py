from datetime import datetime

from pydantic import BaseModel

from app.enums import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    filepath: str
    status: DocumentStatus
    created_at: datetime