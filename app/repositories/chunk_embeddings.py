from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChunkEmbedding, DocumentChunk


class ChunkEmbeddingRepository:
    async def create_for_chunks(
        self,
        db: AsyncSession,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        provider: str,
        model_name: str,
        dimensions: int,
    ) -> list[ChunkEmbedding]:
        embeddings = [
            ChunkEmbedding(
                chunk_id=chunk.id,
                provider=provider,
                model_name=model_name,
                dimensions=dimensions,
                embedding=vector,
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        db.add_all(embeddings)
        await db.flush()
        return embeddings

    async def delete_for_chunks(
        self,
        db: AsyncSession,
        chunks: list[DocumentChunk],
        provider: str,
        model_name: str,
    ) -> None:
        await db.execute(
            delete(ChunkEmbedding).where(
                ChunkEmbedding.chunk_id.in_([chunk.id for chunk in chunks]),
                ChunkEmbedding.provider == provider,
                ChunkEmbedding.model_name == model_name,
            )
        )
        await db.flush()

    async def commit_created_for_chunks(
        self,
        db: AsyncSession,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        provider: str,
        model_name: str,
        dimensions: int,
    ) -> list[ChunkEmbedding]:
        embeddings = await self.create_for_chunks(
            db=db,
            chunks=chunks,
            vectors=vectors,
            provider=provider,
            model_name=model_name,
            dimensions=dimensions,
        )
        await db.commit()
        return embeddings
