from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import get_health_service
from app.services import HealthService

router = APIRouter()


@router.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    service: HealthService = Depends(get_health_service),
):
    return await service.check(db)
