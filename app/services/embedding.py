import httpx

from app.core import settings
from app.enums import LLMProvider


class EmbeddingService:
    def __init__(
        self,
        provider: LLMProvider = settings.EMBEDDING_PROVIDER,
        model_name: str = settings.EMBEDDING_MODEL,
        dimensions: int = settings.EMBEDDING_DIM,
        base_url: str = settings.EMBEDDING_BASE_URL,
        api_key: str = settings.EMBEDDING_API_KEY,
    ):
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")

        self.provider = provider.lower()
        self.model_name = model_name
        self._dimensions = dimensions
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        
    # expose read-only API
    # but keep internal mutability control
    # avoids accidental runtime reconfiguration bugs
    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_text(
        self,
        text: str,
    ) -> list[float]:
        if not text.strip():
            return [0.0] * self.dimensions

        if self.provider == LLMProvider.OLLAMA:
            return await self._embed_ollama(text)

        if self.provider == LLMProvider.OPENROUTER:
            return await self._embed_openrouter(text)

        if self.provider == LLMProvider.GEMINI:
            return await self._embed_gemini(text)

        if self.provider == LLMProvider.GROQ:
            raise ValueError(
                "GroqAIProvider is supported for chat, but embeddings are not implemented for Groq."
            )

        raise ValueError(
            f"Unsupported embedding provider: {self.provider}"
        )

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            await self.embed_text(text)
            for text in texts
        ]

    async def _embed_ollama(
        self,
        text: str,
    ) -> list[float]:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["embedding"]

    async def _embed_openrouter(
        self,
        text: str,
    ) -> list[float]:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": text,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["data"][0]["embedding"]

    async def _embed_gemini(
        self,
        text: str,
    ) -> list[float]:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.model_name}:embedContent",
                params={
                    "key": self.api_key,
                },
                json={
                    "content": {
                        "parts": [
                            {
                                "text": text,
                            }
                        ]
                    },
                    "outputDimensionality": self.dimensions,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["embedding"]["values"]