import os
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_document_repository,
    get_owned_project,
)
from app.models import Document
from app.repositories import DocumentRepository
from app.schemas import DocumentResponse

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------------------------------
# GET DOCUMENTS
# -------------------------------------------------
@router.get(
    "/projects/{project_id}/documents",
    response_model=List[DocumentResponse],
)
async def get_documents(
    db: AsyncSession = Depends(get_db),
    project=Depends(get_owned_project),
    documents: DocumentRepository = Depends(
        get_document_repository
    ),
):
    return await documents.list_for_project(project.id, db)

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
    project=Depends(get_owned_project),
    documents: DocumentRepository = Depends(
        get_document_repository
    ),
):
    # save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    document = Document(
        project_id=project.id,
        filename=file.filename,
        filepath=file_path,
        status="uploaded",
    )

    document = await documents.create(db, document)
    await db.commit()
    await db.refresh(document)

    return document