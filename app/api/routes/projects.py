from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)

router = APIRouter()

fake_projects = [
    {
        "id": 1,
        "name": "AI Assistant",
        "description": "Research AI",
        "user_id": 1,
        "created_at": datetime.now(timezone.utc),
    }
]


@router.get(
    "/",
    response_model=List[ProjectResponse],
)
async def get_projects():
    return fake_projects


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: ProjectCreate,
):
    new_project = {
        "id": len(fake_projects) + 1,
        "name": payload.name,
        "description": payload.description,
        "user_id": 1,
        "created_at": datetime.now(timezone.utc),
    }

    fake_projects.append(new_project)

    return new_project


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    project_id: int,
):
    for project in fake_projects:
        if project["id"] == project_id:
            return project

    raise HTTPException(
        status_code=404,
        detail="Project not found",
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: int,
):
    for index, project in enumerate(fake_projects):
        if project["id"] == project_id:
            fake_projects.pop(index)
            return

    raise HTTPException(
        status_code=404,
        detail="Project not found",
    )