from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import Project
from app.schemas import ProjectCreate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.user_id == user.id)
    )
    return result.scalars().all()

@router.post("/", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    project = Project(
        name=payload.name,
        description=payload.description,
        user_id=user.id,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id
        )
    )

    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user.id
        )
    )

    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    await db.delete(project)
    await db.commit()