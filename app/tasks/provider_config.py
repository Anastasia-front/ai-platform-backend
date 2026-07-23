from sqlalchemy.ext.asyncio import AsyncSession

from app.services.provider_config import provider_config


async def load_provider_config(db: AsyncSession) -> None:
    await provider_config.load_from_db(db)
