from pydantic import BaseModel


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int