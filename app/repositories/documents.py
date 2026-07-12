from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import DocumentStatus, EmbeddingStatus
from app.models import Document, Project


class DocumentRepository:

    async def create(
        self,
        db: AsyncSession,
        document: Document,
    ):
        db.add(document)
        await db.flush()

        return document

    async def get_by_id(
        self,
        db: AsyncSession,
        document_id: int,
    ):
        result = await db.execute(
            select(Document).where(
                Document.id == document_id
            )
        )

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
    ):
        result = await db.execute(
            select(Document)
            .join(
                Project,
                Project.id == Document.project_id,
            )
            .where(
                Document.id == document_id,
                Project.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_project(
        self,
        db: AsyncSession,
        project_id: int,
    ):
        result = await db.execute(
            select(Document)
            .where(
                Document.project_id == project_id
            )
            .order_by(Document.id.desc())
        )

        return result.scalars().all()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: int,
    ):
        result = await db.execute(
            select(Document)
            .join(
                Project,
                Project.id == Document.project_id,
            )
            .where(
                Project.user_id == user_id,
            )
            .order_by(Document.id.desc())
        )

        return result.scalars().all()

    async def delete(
        self,
        db: AsyncSession,
        document: Document,
    ):
        await db.delete(document)

        await db.flush()

    async def save_uploaded(
        self,
        db: AsyncSession,
        document: Document,
    ) -> Document:
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    async def queue_processing(
        self,
        db: AsyncSession,
        document: Document,
    ) -> Document:
        document.status = DocumentStatus.QUEUED
        document.processing_error = None
        await db.commit()
        await db.refresh(document)
        return document

    async def restore_uploaded(
        self,
        db: AsyncSession,
        document: Document,
    ) -> Document:
        document.status = DocumentStatus.UPLOADED
        await db.commit()
        await db.refresh(document)
        return document

    async def set_task_id(
        self,
        db: AsyncSession,
        document: Document,
        task_id: str,
    ) -> Document:
        document.celery_task_id = task_id
        await db.commit()
        await db.refresh(document)
        return document

    async def start_processing(
        self,
        db: AsyncSession,
        document: Document,
        started_at: datetime,
    ) -> None:
        document.status = DocumentStatus.PROCESSING
        document.processing_started_at = started_at
        document.embedding_status = EmbeddingStatus.PROCESSING
        await db.flush()

    async def complete_processing(
        self,
        db: AsyncSession,
        document: Document,
        text: str,
        finished_at: datetime,
        duration_ms: int,
    ) -> Document:
        document.text = text
        document.status = DocumentStatus.INDEXED
        document.embedding_status = EmbeddingStatus.COMPLETED
        document.processing_finished_at = finished_at
        document.processing_duration_ms = duration_ms
        await db.commit()
        await db.refresh(document)
        return document

    async def fail_processing(
        self,
        db: AsyncSession,
        document: Document,
        error: str | None = None,
    ) -> Document:
        document.status = DocumentStatus.FAILED
        document.embedding_status = EmbeddingStatus.FAILED
        document.processing_error = error
        await db.commit()
        await db.refresh(document)
        return document

    async def rollback(self, db: AsyncSession) -> None:
        await db.rollback()
