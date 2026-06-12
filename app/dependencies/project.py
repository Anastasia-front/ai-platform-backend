from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.repositories import ProjectRepository

projects = ProjectRepository()


async def get_owned_project(
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
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project