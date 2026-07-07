import asyncio

import httpx

from app.enums import EmbeddingProvider
from app.services.provider_config import provider_config


class EmbeddingService:
    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        model_name: str | None = None,
        dimensions: int | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        config = provider_config.embeddings
        if dimensions is None:
            dimensions = config.dimensions

        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")

        self.provider = (provider or config.provider).lower()
        self.model_name = model_name or config.model
        self._dimensions = dimensions
        self.base_url = (base_url or config.base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else config.api_key

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

        if self.provider == EmbeddingProvider.OLLAMA:
            return await self._embed_ollama(text)

        if self.provider == EmbeddingProvider.OPENROUTER:
            return await self._embed_openrouter(text)

        if self.provider == EmbeddingProvider.GEMINI:
            return await self._embed_gemini(text)

        if self.provider == EmbeddingProvider.GROQ:
            raise ValueError(
                "GroqAIProvider is supported for chat, but embeddings are not implemented for Groq."
            )

        raise ValueError(f"Unsupported embedding provider: {self.provider}")

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        vectors = []

        for text in texts:
            vector = await self.embed_text(text)
            vectors.append(vector)

            await asyncio.sleep(0.2)

        return vectors

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
        last_error = None

        for attempt in range(3):
            try:
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

            except httpx.HTTPStatusError as exc:
                last_error = exc

                if exc.response.status_code in {429, 500, 502, 503, 504}:
                    await asyncio.sleep(2**attempt)
                    continue

                raise

            except httpx.HTTPError as exc:
                last_error = exc
                await asyncio.sleep(2**attempt)
                continue

        raise last_error
