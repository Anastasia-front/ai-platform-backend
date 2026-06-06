import os
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes import projects
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import Document
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
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    project = await projects.get_for_user(
        db,
        project_id,
        user.id,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )

    return result.scalars().all()


# -------------------------------------------------
# UPLOAD DOCUMENT
# -------------------------------------------------
@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # verify ownership
    project_result = await projects.get_for_user(
        db,
        project_id,
        user.id,
    )

    if not project_result:
        raise HTTPException(status_code=404, detail="Project not found")

    # save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    document = Document(
        project_id=project_id,
        filename=file.filename,
        filepath=file_path,
        status="uploaded",
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document