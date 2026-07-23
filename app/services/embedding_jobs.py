from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import EmbeddingStatus
from app.models import Document, Project
from app.services.background_jobs import BackgroundJobService
from app.tasks.embeddings import (
    _rebuild_document_embeddings,
    _sync_project_embeddings,
)


class EmbeddingJobService:
    async def rebuild_document(
        self,
        db: AsyncSession,
        *,
        document: Document,
        background_tasks: BackgroundTasks,
        force: bool = True,
    ) -> dict:
        return await self._enqueue_document_rebuild(
            db=db,
            document=document,
            background_tasks=background_tasks,
            force=force,
            cancellable=False,
        )

    async def resume_document_rebuild(
        self,
        db: AsyncSession,
        *,
        document: Document,
        background_tasks: BackgroundTasks,
    ) -> dict:
        return await self._enqueue_document_rebuild(
            db=db,
            document=document,
            background_tasks=background_tasks,
            force=False,
            cancellable=True,
        )

    async def retry_document_rebuild(
        self,
        db: AsyncSession,
        *,
        document: Document,
        background_tasks: BackgroundTasks,
    ) -> dict:
        return await self._enqueue_document_rebuild(
            db=db,
            document=document,
            background_tasks=background_tasks,
            force=True,
            cancellable=True,
        )

    async def cancel_document_rebuild(
        self,
        db: AsyncSession,
        *,
        document: Document,
        jobs: BackgroundJobService,
    ) -> dict:
        if document.embedding_status in (
            EmbeddingStatus.QUEUED,
            EmbeddingStatus.PROCESSING,
            EmbeddingStatus.CANCELLING,
        ):
            await self._ensure_embedding_cancellation_statuses(db)
            if document.embedding_status != EmbeddingStatus.CANCELLED:
                document.embedding_status = EmbeddingStatus.CANCELLING
                await db.commit()
                await db.refresh(document)

            if document.celery_task_id and not document.celery_task_id.startswith("local-"):
                jobs.revoke(document.celery_task_id, terminate=True)

            document.embedding_status = EmbeddingStatus.CANCELLED
            document.celery_task_id = None
            await db.commit()
            await db.refresh(document)

        return self._document_response(document)

    async def sync_project(
        self,
        db: AsyncSession,
        *,
        project: Project,
        background_tasks: BackgroundTasks,
    ) -> dict:
        return await self._enqueue_project_sync(
            db=db,
            project=project,
            background_tasks=background_tasks,
        )

    async def resume_project_sync(
        self,
        db: AsyncSession,
        *,
        project: Project,
        background_tasks: BackgroundTasks,
    ) -> dict:
        return await self._enqueue_project_sync(
            db=db,
            project=project,
            background_tasks=background_tasks,
        )

    async def retry_project_sync(
        self,
        db: AsyncSession,
        *,
        project: Project,
        background_tasks: BackgroundTasks,
    ) -> dict:
        return await self._enqueue_project_sync(
            db=db,
            project=project,
            background_tasks=background_tasks,
        )

    async def cancel_project_sync(
        self,
        db: AsyncSession,
        *,
        project: Project,
        jobs: BackgroundJobService,
    ) -> dict:
        if project.embedding_sync_status in (
            EmbeddingStatus.QUEUED,
            EmbeddingStatus.PROCESSING,
            EmbeddingStatus.CANCELLING,
        ):
            await self._ensure_embedding_cancellation_statuses(db)
            project.embedding_sync_status = EmbeddingStatus.CANCELLING
            await db.commit()
            await db.refresh(project)

            if (
                project.embedding_sync_task_id
                and not project.embedding_sync_task_id.startswith("local-")
            ):
                jobs.revoke(project.embedding_sync_task_id, terminate=True)

            project.embedding_sync_status = EmbeddingStatus.CANCELLED
            project.embedding_sync_task_id = None
            await db.commit()
            await db.refresh(project)

        return self.project_sync_status(project)

    def project_sync_status(self, project: Project) -> dict:
        return {
            "project_id": project.id,
            "status": project.embedding_sync_status,
            "task_id": project.embedding_sync_task_id,
            "error": project.embedding_sync_error,
        }

    async def _enqueue_document_rebuild(
        self,
        db: AsyncSession,
        *,
        document: Document,
        background_tasks: BackgroundTasks,
        force: bool,
        cancellable: bool,
    ) -> dict:
        blocked_statuses = [EmbeddingStatus.QUEUED, EmbeddingStatus.PROCESSING]
        if cancellable:
            blocked_statuses.append(EmbeddingStatus.CANCELLING)

        if document.embedding_status not in tuple(blocked_statuses):
            document.embedding_status = EmbeddingStatus.QUEUED
            document.processing_error = None
            document.celery_task_id = f"local-embedding-{uuid4()}"
            await db.commit()
            await db.refresh(document)

            background_tasks.add_task(
                _rebuild_document_embeddings,
                document.id,
                document.celery_task_id,
                force,
            )

        return self._document_response(document)

    async def _enqueue_project_sync(
        self,
        db: AsyncSession,
        *,
        project: Project,
        background_tasks: BackgroundTasks,
    ) -> dict:
        if project.embedding_sync_status not in (
            EmbeddingStatus.QUEUED,
            EmbeddingStatus.PROCESSING,
            EmbeddingStatus.CANCELLING,
        ):
            project.embedding_sync_status = EmbeddingStatus.QUEUED
            project.embedding_sync_error = None
            project.embedding_sync_task_id = f"local-embedding-sync-{uuid4()}"
            await db.commit()
            await db.refresh(project)

            background_tasks.add_task(
                _sync_project_embeddings,
                project.id,
                project.embedding_sync_task_id,
            )

        return self.project_sync_status(project)

    async def _ensure_embedding_cancellation_statuses(self, db: AsyncSession) -> None:
        await db.execute(
            text("ALTER TYPE embeddingstatus ADD VALUE IF NOT EXISTS 'cancelling'")
        )
        await db.commit()
        await db.execute(
            text("ALTER TYPE embeddingstatus ADD VALUE IF NOT EXISTS 'cancelled'")
        )
        await db.commit()

    def _document_response(self, document: Document) -> dict:
        return {
            "document_id": document.id,
            "status": document.embedding_status,
            "task_id": document.celery_task_id,
        }
