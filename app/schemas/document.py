from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import DocumentStatus, EmbeddingStatus


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
    chunk_count: int | None = None
    first_chunk_index: int | None = None
    last_chunk_index: int | None = None

    model_config = ConfigDict(from_attributes=True)

class DocumentProcessingResponse(BaseModel):
    id: int
    status: DocumentStatus
    processing_started_at: datetime | None = None
    processing_finished_at: datetime | None = None
    processing_duration_ms: int | None = None
    embedding_status: EmbeddingStatus
    chunk_count: int | None = None