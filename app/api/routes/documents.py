from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_document_chunk_repository,
    get_document_repository,
    get_owned_document,
    get_owned_project,
)
from app.models import Document, Project
from app.repositories import DocumentChunkRepository, DocumentRepository
from app.schemas import (
    DocumentChunkResponse,
    DocumentProcessingResponse,
    DocumentResponse,
)
from app.services import DocumentService

router = APIRouter()


# -------------------------------------------------
# GET DOCUMENTS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/documents",
    response_model=List[DocumentResponse],
)
async def get_documents(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    documents: DocumentRepository = Depends(get_document_repository),
):
    return await documents.list_for_project(db, project.id)


# -------------------------------------------------
# UPLOAD DOCUMENT
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
):
    service = DocumentService()

    return await service.upload(
        db,
        project,
        file,
    )


# -------------------------------------------------
# PROCESS DOCUMENT
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/process",
    response_model=DocumentProcessingResponse,
)
async def process_document(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    documents: DocumentRepository = Depends(get_document_repository),
    chunks: DocumentChunkRepository = Depends(get_document_chunk_repository),
):
    service = DocumentService(documents=documents)

    try:
        document = await service.process(
            db,
            document,
        )

        chunk_count = await chunks.count_for_document(db, document.id)

        return DocumentProcessingResponse(
            id=document.id,
            status=document.status,
            processing_started_at=document.processing_started_at,
            processing_finished_at=document.processing_finished_at,
            processing_duration_ms=document.processing_duration_ms,
            embedding_status=document.embedding_status,
            chunk_count=chunk_count,
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# -------------------------------------------------
# GET DOCUMENT CHUNKS
# -------------------------------------------------
@router.get(
    "/documents/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
)
async def get_document_chunks(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    chunks: DocumentChunkRepository = Depends(get_document_chunk_repository),
):
    return await chunks.list_for_document(
        db,
        document.id,
    )


# -------------------------------------------------
# DELETE DOCUMENT
# -------------------------------------------------
@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    documents: DocumentRepository = Depends(get_document_repository),
):
    await documents.delete(
        db,
        document,
    )
    await db.commit()
