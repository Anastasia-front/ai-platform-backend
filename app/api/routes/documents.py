from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, File, UploadFile, status

from app.schemas.document import DocumentResponse

router = APIRouter()


@router.get(
    "/projects/{project_id}/documents",
    response_model=List[DocumentResponse],
)
async def get_documents(
    project_id: int,
):
    return [
        {
            "id": 1,
            "project_id": project_id,
            "filename": "manual.pdf",
            "filepath": "/uploads/manual.pdf",
            "status": "indexed",
            "created_at": datetime.now(timezone.utc),
        }
    ]


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
):
    return {
        "id": 1,
        "project_id": project_id,
        "filename": file.filename,
        "filepath": f"/uploads/{file.filename}",
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc),
    }