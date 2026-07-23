from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_background_job_service,
    get_document_chunk_repository,
    get_document_repository,
    get_document_service,
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
from app.services import BackgroundJobService, DocumentService

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
    service: DocumentService = Depends(get_document_service),
):
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
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_document(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    service: DocumentService = Depends(get_document_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    return await service.enqueue_processing_response(db, document, jobs)

# -------------------------------------------------
# CANCEL PROCESS DOCUMENT
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/process/cancel",
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_document_processing(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    service: DocumentService = Depends(get_document_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    return await service.cancel_processing(db, document, jobs)

# -------------------------------------------------
# RETRY PROCESS DOCUMENT
# -------------------------------------------------
@router.post(
    "/documents/{document_id}/process/retry",
    response_model=DocumentProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_processing(
    db: AsyncSession = Depends(get_db),
    document: Document = Depends(get_owned_document),
    service: DocumentService = Depends(get_document_service),
    jobs: BackgroundJobService = Depends(get_background_job_service),
):
    return await service.retry_processing(db, document, jobs)


# -------------------------------------------------
# GET SINGLE DOCUMENT
# -------------------------------------------------
@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document(
    document: Document = Depends(get_owned_document),
):
    return document


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
    service: DocumentService = Depends(get_document_service),
):
    await service.delete(db, document)
