import hashlib
import math


class EmbeddingService:
    def __init__(
        self,
        dimensions: int = 384,
        model_name: str = "local-hash-placeholder",
    ):
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than 0")

        self.dimensions = dimensions
        self.model_name = model_name

    async def embed_text(
        self,
        text: str,
    ) -> list[float]:
        if not text.strip():
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions

        for token in text.lower().split():
            digest = hashlib.blake2b(
                token.encode("utf-8"),
                digest_size=16,
            ).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))

        if magnitude == 0:
            return vector

        return [value / magnitude for value in vector]

    async def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            await self.embed_text(text)
            for text in texts
        ]
