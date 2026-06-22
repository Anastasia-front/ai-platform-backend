import mimetypes
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE,
)
from app.enums import DocumentStatus, EmbeddingStatus
from app.models import ChunkEmbedding, Document, DocumentChunk, Project
from app.repositories import (
    DocumentChunkRepository,
    DocumentRepository,
)
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

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large.",
            )

        original_filename = self._safe_filename(file.filename)
        print(file.content_type)
        extension = Path(original_filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file extension.",
            )

        mime_type = (
            file.content_type
            or mimetypes.guess_type(original_filename)[0]
            or "application/octet-stream"
        )

        if mime_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type.",
            )

        stored_filename = self._stored_filename(original_filename)

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = self.upload_dir / stored_filename

        with open(file_path, "wb") as uploaded_file:
            uploaded_file.write(content)

        document = Document(
            project_id=project.id,
            filename=original_filename,
            filepath=str(file_path),
            mime_type=mime_type,
            file_size=len(content),
            status=DocumentStatus.UPLOADED,
        )

        document = await self.documents.create(
            db,
            document,
        )

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
        started = datetime.now(timezone.utc)

        document.processing_started_at = started
        document.embedding_status = EmbeddingStatus.PROCESSING
        await db.flush()

        try:
            # 1. extract full text
            text = await self.extract_text(document)

            # 2. create chunks (in memory)
            chunk_objs = self.chunk_document(
                document=document,
                text=text,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            # 3. persist chunks FIRST (so they get IDs)
            await self.chunks.create_many(db, chunk_objs)
            await db.flush()  # IMPORTANT: ensures IDs exist

            # 4. generate embeddings
            embeddings_vectors = await self.embeddings.embed_texts(
                [chunk.text for chunk in chunk_objs]
            )

            # 5. create embedding rows using REAL chunk IDs
            embedding_rows = [
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    model_name=self.embeddings.model_name,
                    embedding=vector,
                )
                for chunk, vector in zip(chunk_objs, embeddings_vectors)
            ]

            db.add_all(embedding_rows)
            await db.flush()

            # 6. finalize document
            document.text = text
            document.status = DocumentStatus.INDEXED

            finished = datetime.now(timezone.utc)

            document.processing_finished_at = finished
            document.processing_duration_ms = int(
                (finished - started).total_seconds() * 1000
            )

            document.embedding_status = EmbeddingStatus.COMPLETED

            await db.commit()
            await db.refresh(document)

            return document

        except Exception:
            await db.rollback()

            document.status = DocumentStatus.FAILED
            document.embedding_status = EmbeddingStatus.FAILED

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
            f"Unsupported document type: " f"{file_path.suffix or document.mime_type}"
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
                text,
                chunk_size,
                overlap,
            )
        ]

    def _safe_filename(
        self,
        filename: str | None,
    ) -> str:
        name = Path(filename or "document").name

        safe_name = re.sub(
            r"[^\w.\-]+",
            "_",
            name,
            flags=re.UNICODE,
        ).strip("._")

        return safe_name or "document"

    def _stored_filename(
        self,
        filename: str,
    ) -> str:
        suffix = Path(filename).suffix.lower()

        return f"{uuid4()}{suffix}"
