from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_current_user,
    get_document_chunk_repository,
    get_document_repository,
    get_owned_project,
)
from app.models import Project, User
from app.repositories import DocumentChunkRepository, DocumentRepository
from app.schemas import DocumentChunkResponse, DocumentResponse
from app.services import DocumentService

router = APIRouter()


# -------------------------------------------------
# GET DOCUMENTS
# -------------------------------------------------
@router.get(
    "/{project_id}/documents",
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
    "/{project_id}/documents",
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
        db=db,
        project=project,
        file=file,
    )


# -------------------------------------------------
# PROCESS DOCUMENT
# -------------------------------------------------
@router.post(
    "/{project_id}/documents/{document_id}/process",
    response_model=DocumentResponse,
)
async def process_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    project: Project = Depends(get_owned_project),
    documents: DocumentRepository = Depends(get_document_repository),
):
    document = await documents.get_for_user(
        db=db,
        document_id=document_id,
        user_id=user.id,
    )

    if not document or document.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    service = DocumentService(documents=documents)

    try:
        return await service.process(
            db=db,
            document=document,
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
    "/{project_id}/documents/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
)
async def get_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    project: Project = Depends(get_owned_project),
    documents: DocumentRepository = Depends(get_document_repository),
    chunks: DocumentChunkRepository = Depends(get_document_chunk_repository),
):
    document = await documents.get_for_user(
        db=db,
        document_id=document_id,
        user_id=user.id,
    )

    if not document or document.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return await chunks.list_for_document(
        db=db,
        document_id=document.id,
    )
