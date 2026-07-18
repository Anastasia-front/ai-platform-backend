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
    embedding_status: EmbeddingStatus
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    embeddings_updated_at: datetime | None = None
    processing_error: str | None = None
    text: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentProcessingResponse(BaseModel):
    id: int
    status: DocumentStatus
    celery_task_id: str | None = None
    processing_started_at: datetime | None = None
    processing_finished_at: datetime | None = None
    processing_duration_ms: int | None = None
    processing_error: str | None = None
    embedding_status: EmbeddingStatus
    chunk_count: int | None = None
