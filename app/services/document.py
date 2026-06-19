import mimetypes
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import DocumentStatus
from app.models import Document, DocumentChunk, Project
from app.repositories import DocumentChunkRepository, DocumentRepository
from app.services.chunk import ChunkService
from app.services.embedding import EmbeddingService

from .extractors import DEFAULT_EXTRACTORS, TextExtractor


class DocumentService:
    def __init__(
        self,
        upload_dir: str = "uploads",
        documents: DocumentRepository | None = None,
        chunks: DocumentChunkRepository | None = None,
        chunker: ChunkService | None = None,
        embeddings: EmbeddingService | None = None,
        extractors: tuple[TextExtractor, ...] = DEFAULT_EXTRACTORS,
    ):
        self.upload_dir = Path(upload_dir)
        self.documents = documents or DocumentRepository()
        self.chunks = chunks or DocumentChunkRepository()
        self.chunker = chunker or ChunkService()
        self.embeddings = embeddings or EmbeddingService()
        self.extractors = extractors

    async def upload(
        self,
        db: AsyncSession,
        project: Project,
        file: UploadFile,
    ) -> Document:
        content = await file.read()
        original_filename = self._safe_filename(file.filename)
        stored_filename = self._stored_filename(original_filename)
        file_path = self.upload_dir / stored_filename

        self.upload_dir.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as uploaded_file:
            uploaded_file.write(content)

        mime_type = (
            file.content_type
            or mimetypes.guess_type(original_filename)[0]
            or "application/octet-stream"
        )

        document = Document(
            project_id=project.id,
            filename=original_filename,
            filepath=str(file_path),
            mime_type=mime_type,
            file_size=len(content),
            status=DocumentStatus.UPLOADED,
        )

        document = await self.documents.create(db, document)
        await db.commit()
        await db.refresh(document)

        return document

    async def process(
        self,
        db: AsyncSession,
        document: Document,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> Document:
        document.status = DocumentStatus.PROCESSING
        await db.flush()

        try:
            text = await self.extract_text(document)
            chunks = self.chunk_document(
                document=document,
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            await self.embeddings.embed_texts(
                [
                    chunk.text
                    for chunk in chunks
                ]
            )

            await self.chunks.delete_for_document(db, document.id)
            await self.chunks.create_many(db, chunks)

            document.text = text
            document.status = DocumentStatus.INDEXED

            await db.commit()
            await db.refresh(document)

            return document

        except Exception:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            db.add(document)
            await db.commit()
            await db.refresh(document)
            raise

    async def extract_text(
        self,
        document: Document,
    ) -> str:
        file_path = Path(document.filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {document.filepath}")

        for extractor in self.extractors:
            if extractor.supports(
                file_path=file_path,
                mime_type=document.mime_type,
            ):
                return extractor.extract(file_path)

        raise ValueError(
            f"Unsupported document type: {file_path.suffix or document.mime_type}"
        )

    def chunk_document(
        self,
        document: Document,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                token_count=chunk.token_count,
            )
            for chunk in self.chunker.chunk(
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        ]

    def _safe_filename(
        self,
        filename: str | None,
    ) -> str:
        name = Path(filename or "document").name
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")

        return safe_name or "document"

    def _stored_filename(
        self,
        filename: str,
    ) -> str:
        suffix = Path(filename).suffix.lower()

        return f"{uuid4().hex}{suffix}"
