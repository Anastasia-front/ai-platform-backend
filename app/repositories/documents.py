from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, Project


class DocumentRepository:

    async def create(
        self,
        db: AsyncSession,
        **data,
    ):
        document = Document(**data)

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