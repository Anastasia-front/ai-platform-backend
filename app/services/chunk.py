from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    token_count: int


class ChunkService:

    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[TextChunk]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap must be greater than or equal to 0")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        normalized_text = self._normalize(text)

        if not normalized_text:
            return []

        chunks: list[TextChunk] = []
        start = 0
        chunk_index = 0

        while start < len(normalized_text):
            end = min(start + chunk_size, len(normalized_text))
            chunk_text = normalized_text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        text=chunk_text,
                        token_count=self.count_tokens(chunk_text),
                    )
                )
                chunk_index += 1

            if end >= len(normalized_text):
                break

            start = end - overlap

        return chunks

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def _normalize(self, text: str) -> str:
        return "\n".join(
            line.rstrip()
            for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        ).strip()
