from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import EmbeddingProvider
from app.models import ChunkEmbedding, Document, DocumentChunk, Project


class RetrievalRepository:

    async def search(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        user_id: int,
        embedding: list[float],
        provider: EmbeddingProvider,
        model_name: str,
        top_k: int,
    ):
        distance = ChunkEmbedding.embedding.cosine_distance(embedding)

        result = await db.execute(
            select(
                DocumentChunk,
                Document.filename.label("document_name"),
                distance.label("score"),
            )
            .join(
                ChunkEmbedding,
                ChunkEmbedding.chunk_id == DocumentChunk.id,
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .join(
                Project,
                Project.id == Document.project_id,
            )
            .where(
                Document.project_id == project_id,
                Project.user_id == user_id,
                ChunkEmbedding.provider == provider,
                ChunkEmbedding.model_name == model_name,
            )
            .order_by(distance)
            .limit(top_k)
        )

        return result.all()
