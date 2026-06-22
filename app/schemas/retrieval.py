from pydantic import BaseModel, ConfigDict


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5

class RetrievalResult(BaseModel):
    document_id: int
    chunk_id: int
    chunk_index: int
    score: float
    text: str

    model_config = ConfigDict(from_attributes=True)


class RetrievalResponse(BaseModel):
    results: list[RetrievalResult]