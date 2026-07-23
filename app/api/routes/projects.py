from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import (
    get_current_user,
    get_owned_project,
    get_project_repository,
    get_project_update_service,
    get_retrieval_service,
)
from app.models import Project, User
from app.repositories import ProjectRepository
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RetrievalRequest,
    RetrievalResponse,
)
from app.services import ProjectUpdateService, RetrievalService

router = APIRouter()

# -------------------------------------------------
# CREATE PROJECT
# -------------------------------------------------
@router.post(
    "/", 
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ProjectUpdateService = Depends(get_project_update_service),
):
    return await service.create(
        db=db,
        payload=payload,
        user_id=user.id,
    )

# -------------------------------------------------
#  GET SINGLE PROJECT
# -------------------------------------------------
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project: Project = Depends(get_owned_project),
):
    return project


# -------------------------------------------------
# UPDATE PROJECT
# -------------------------------------------------
@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    service: ProjectUpdateService = Depends(get_project_update_service),
):
    return await service.update(
        db=db,
        project=project,
        payload=payload,
    )

# -------------------------------------------------
#  GET PROJECTS
# -------------------------------------------------
@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    projects: ProjectRepository = Depends(
        get_project_repository
    )
):
    return await projects.list_for_user(
        db,
        user.id,
    )   

# -------------------------------------------------
#  RETRIEVE PROJECTS
# -------------------------------------------------
@router.post(
    "/{project_id}/retrieve",
    response_model=RetrievalResponse,
)
async def retrieve(
    request: RetrievalRequest,
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
):
    return await retrieval_service.retrieve(
        db=db,
        project_id=project.id,
        user_id=current_user.id,
        query=request.query,
        top_k=request.top_k,
    )

# -------------------------------------------------
# DELETE PROJECT
# -------------------------------------------------
@router.delete(
    "/{project_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    db: AsyncSession = Depends(get_db),
    project: Project = Depends(get_owned_project),
    service: ProjectUpdateService = Depends(get_project_update_service),
):
    await service.delete(db, project)
