from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentChunkBase(BaseModel):
    chunk_index: int
    text: str
    token_count: int


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    document_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
