from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import DocumentStatus


class DocumentBase(BaseModel):
    filename: str
    filepath: str
    mime_type: str
    file_size: int


class DocumentResponse(DocumentBase):
    id: int
    project_id: int

    status: DocumentStatus

    text: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)