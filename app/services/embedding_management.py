from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChunkEmbedding, DocumentChunk
from app.services.embedding import EmbeddingService


class EmbeddingManagementService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
    ):
        self.embedding_service = embedding_service

    async def rebuild_document_embeddings(
        self,
        db: AsyncSession,
        *,
        document_id: int,
    ) -> int:
        provider = self.embedding_service.provider
        model_name = self.embedding_service.model_name

        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )

        chunks = result.scalars().all()

        await db.execute(
            delete(ChunkEmbedding)
            .where(
                ChunkEmbedding.chunk_id.in_(
                    [chunk.id for chunk in chunks]
                ),
                ChunkEmbedding.provider == provider,
                ChunkEmbedding.model_name == model_name,
            )
        )

        vectors = await self.embedding_service.embed_texts(
            [chunk.text for chunk in chunks]
        )

        db.add_all(
            [
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    provider=provider,
                    model_name=model_name,
                    dimensions=self.embedding_service.dimensions,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, vectors)
            ]
        )

        await db.commit()

        return len(chunks)

    async def sync_project_embeddings(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> int:
        provider = self.embedding_service.provider
        model_name = self.embedding_service.model_name

        result = await db.execute(
            select(DocumentChunk)
            .outerjoin(
                ChunkEmbedding,
                (
                    (ChunkEmbedding.chunk_id == DocumentChunk.id)
                    & (ChunkEmbedding.provider == provider)
                    & (ChunkEmbedding.model_name == model_name)
                ),
            )
            .where(
                DocumentChunk.document.has(project_id=project_id),
                ChunkEmbedding.id.is_(None),
            )
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
        )

        chunks = result.scalars().all()

        vectors = await self.embedding_service.embed_texts(
            [chunk.text for chunk in chunks]
        )

        db.add_all(
            [
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    provider=provider,
                    model_name=model_name,
                    dimensions=self.embedding_service.dimensions,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, vectors)
            ]
        )

        await db.commit()

        return len(chunks)