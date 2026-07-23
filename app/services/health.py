from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthService:
    async def check(self, db: AsyncSession) -> dict:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
        }
