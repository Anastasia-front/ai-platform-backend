from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProviderConfig


class ProviderConfigRepository:
    async def list_all(self, db: AsyncSession) -> list[ProviderConfig]:
        result = await db.execute(select(ProviderConfig))
        return list(result.scalars().all())

    async def get(
        self,
        db: AsyncSession,
        kind: str,
        provider: str,
    ) -> ProviderConfig | None:
        result = await db.execute(
            select(ProviderConfig).where(
                ProviderConfig.kind == kind,
                ProviderConfig.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, db: AsyncSession, row: ProviderConfig) -> ProviderConfig:
        db.add(row)
        await db.flush()
        return row

    async def commit(self, db: AsyncSession) -> None:
        await db.commit()
