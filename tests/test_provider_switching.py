from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _fake_session_ctx(fake_db):
    @asynccontextmanager
    async def _ctx():
        yield fake_db

    return _ctx


@pytest.mark.asyncio
async def test_ai_dependency_reloads_provider_config_before_building_service():
    from app.dependencies import services

    fake_db = MagicMock()

    with patch.object(services.provider_config, "load_from_db", AsyncMock()) as load, \
         patch.object(services, "AIService") as ai_service:
        service = await services.get_ai_service(fake_db)

    load.assert_awaited_once_with(fake_db)
    ai_service.assert_called_once_with()
    assert service is ai_service.return_value


@pytest.mark.asyncio
async def test_embedding_dependency_reloads_provider_config_before_building_service():
    from app.dependencies import services

    fake_db = MagicMock()

    with patch.object(services.provider_config, "load_from_db", AsyncMock()) as load, \
         patch.object(services, "EmbeddingService") as embedding_service:
        service = await services.get_embedding_service(fake_db)

    load.assert_awaited_once_with(fake_db)
    embedding_service.assert_called_once_with()
    assert service is embedding_service.return_value


@pytest.mark.asyncio
async def test_startup_preserves_saved_provider_config_instead_of_resyncing_env():
    from app import main

    fake_db = MagicMock()

    with patch.object(main, "AsyncSessionLocal", _fake_session_ctx(fake_db)), \
         patch.object(main.provider_config, "seed_defaults", AsyncMock()) as seed, \
         patch.object(main.provider_config, "sync_settings_to_db", AsyncMock()) as sync, \
         patch.object(main.provider_config, "load_from_db", AsyncMock()) as load, \
         patch.object(main, "recover_running_workflows", AsyncMock()):
        async with main.lifespan(MagicMock()):
            pass

    seed.assert_awaited_once_with(fake_db)
    sync.assert_not_called()
    load.assert_awaited_once_with(fake_db)
