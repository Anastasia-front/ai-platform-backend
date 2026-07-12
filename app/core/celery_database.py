import logging
from collections.abc import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from celery.signals import worker_process_init, worker_process_shutdown
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

_celery_engine: AsyncEngine | None = None
_celery_session_local: async_sessionmaker[AsyncSession] | None = None


def safe_database_url() -> str:
    parsed = urlsplit(settings.DATABASE_URL)
    if parsed.password is None:
        return settings.DATABASE_URL

    username = parsed.username or ""
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{username}:***@{hostname}{port}"
    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def reset_celery_database() -> None:
    global _celery_engine, _celery_session_local
    _celery_engine = None
    _celery_session_local = None


def get_celery_engine() -> AsyncEngine:
    global _celery_engine, _celery_session_local

    if _celery_engine is None:
        _celery_engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            pool_pre_ping=True,
        )
        _celery_session_local = async_sessionmaker(
            bind=_celery_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Initialized Celery database engine for %s", safe_database_url())

    return _celery_engine


def CelerySessionLocal() -> AsyncSession:
    get_celery_engine()
    if _celery_session_local is None:
        raise RuntimeError("Celery session factory was not initialized")
    return _celery_session_local()


async def get_celery_db() -> AsyncGenerator[AsyncSession, None]:
    async with CelerySessionLocal() as session:
        yield session


@worker_process_init.connect
def on_worker_process_init(**_: object) -> None:
    reset_celery_database()


@worker_process_shutdown.connect
def on_worker_process_shutdown(**_: object) -> None:
    reset_celery_database()
