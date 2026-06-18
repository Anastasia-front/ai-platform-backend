from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentChunk


class DocumentChunkRepository:
    async def create_many(
        self,
        db: AsyncSession,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunk]:
        db.add_all(chunks)
        await db.flush()

        return chunks

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
