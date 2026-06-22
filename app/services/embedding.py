import httpx

from app.core import settings


class EmbeddingService:
    def __init__(
        self,
        dimensions: int = 384,
        model_name: str = settings.OLLAMA_EMBEDDING_MODEL,
    ):
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")

        self._dimensions = dimensions
        self.model_name = model_name

    # expose read-only API
    # but keep internal mutability control
    # avoids accidental runtime reconfiguration bugs
    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text,
                },
            )
            return res.json()["embedding"]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed_text(t) for t in texts]
