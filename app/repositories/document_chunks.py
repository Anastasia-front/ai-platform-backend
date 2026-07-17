from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChunkEmbedding, DocumentChunk


class DocumentChunkRepository:
    async def create_many(
        self,
        db: AsyncSession,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        db.add_all(chunks)
        await db.flush()

        return chunks

    async def count_for_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> int:
        result = await db.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id
            )
        )

        return result.scalar_one()

    async def delete_for_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> None:
        await db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
            )
        )
        await db.flush()

    async def list_for_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> list[DocumentChunk]:
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )

        return list(result.scalars().all())

    async def list_missing_embeddings_for_project(
        self,
        db: AsyncSession,
        project_id: int,
        provider: str,
        model_name: str,
    ) -> list[DocumentChunk]:
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

        return list(result.scalars().all())

    async def list_missing_embeddings_for_document(
        self,
        db: AsyncSession,
        document_id: int,
        provider: str,
        model_name: str,
    ) -> list[DocumentChunk]:
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
                DocumentChunk.document_id == document_id,
                ChunkEmbedding.id.is_(None),
            )
            .order_by(DocumentChunk.chunk_index)
        )

        return list(result.scalars().all())
