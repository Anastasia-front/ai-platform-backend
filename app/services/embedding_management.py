from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import ChunkEmbeddingRepository, DocumentChunkRepository
from app.services.embedding import EmbeddingService


class EmbeddingExecutionCancelled(Exception):
    pass


class EmbeddingManagementService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunks: DocumentChunkRepository | None = None,
        chunk_embeddings: ChunkEmbeddingRepository | None = None,
    ):
        self.embedding_service = embedding_service
        self.chunks = chunks or DocumentChunkRepository()
        self.chunk_embeddings = chunk_embeddings or ChunkEmbeddingRepository()

    async def rebuild_document_embeddings(
        self,
        db: AsyncSession,
        *,
        document_id: int,
        force: bool = True,
        should_cancel=None,
    ) -> int:
        provider = self.embedding_service.provider
        model_name = self.embedding_service.model_name

        if force:
            chunks = await self.chunks.list_for_document(db, document_id)

            await self.chunk_embeddings.delete_for_chunks(
                db=db,
                chunks=chunks,
                provider=provider,
                model_name=model_name,
            )
            await db.commit()
        else:
            chunks = await self.chunks.list_missing_embeddings_for_document(
                db=db,
                document_id=document_id,
                provider=provider,
                model_name=model_name,
            )

        return await self._embed_remaining_chunks(
            db=db,
            chunks=chunks,
            provider=provider,
            model_name=model_name,
            should_cancel=should_cancel,
        )

    async def sync_project_embeddings(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        should_cancel=None,
    ) -> int:
        provider = self.embedding_service.provider
        model_name = self.embedding_service.model_name
        dimensions = self.embedding_service.dimensions

        await self.chunk_embeddings.delete_dimension_mismatches_for_project(
            db=db,
            project_id=project_id,
            provider=provider,
            model_name=model_name,
            dimensions=dimensions,
        )
        await db.commit()

        chunks = await self.chunks.list_missing_embeddings_for_project(
            db=db,
            project_id=project_id,
            provider=provider,
            model_name=model_name,
        )

        return await self._embed_remaining_chunks(
            db=db,
            chunks=chunks,
            provider=provider,
            model_name=model_name,
            should_cancel=should_cancel,
        )

    async def _embed_remaining_chunks(
        self,
        db: AsyncSession,
        chunks,
        provider: str,
        model_name: str,
        should_cancel=None,
    ) -> int:
        created = 0

        for chunk in chunks:
            if should_cancel is not None and await should_cancel():
                raise EmbeddingExecutionCancelled()

            vectors = await self.embedding_service.embed_texts([chunk.text])

            actual_provider = self.embedding_service.provider
            actual_model = self.embedding_service.model_name
            if (actual_provider, actual_model) != (provider, model_name):
                if created:
                    raise RuntimeError(
                        "Embedding provider changed after embeddings were committed."
                    )
                provider = actual_provider
                model_name = actual_model

            if should_cancel is not None and await should_cancel():
                raise EmbeddingExecutionCancelled()

            await self.chunk_embeddings.commit_created_for_chunks(
                db=db,
                chunks=[chunk],
                vectors=vectors,
                provider=provider,
                model_name=model_name,
                dimensions=self.embedding_service.dimensions,
            )
            created += 1

        return created
