from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.dependencies import get_current_user
from app.enums import ChatProvider, EmbeddingProvider
from app.models import User
from app.schemas.provider import (
    ChatProviderConfigResponse,
    ChatProviderConfigUpdate,
    EmbeddingProviderConfigResponse,
    EmbeddingProviderConfigUpdate,
    ProviderConfigResponse,
    ProviderHealthResponse,
    ProvidersResponse,
)
from app.services import AIService, EmbeddingService
from app.services.provider_config import provider_config

router = APIRouter()


@router.get("", response_model=ProvidersResponse)
async def list_providers(
    _user: User = Depends(get_current_user),
):
    return provider_config.list_providers()


@router.get("/config", response_model=ProviderConfigResponse)
async def get_provider_config(
    _user: User = Depends(get_current_user),
):
    return provider_config.current_config()


@router.patch("/chat/defaults", response_model=ChatProviderConfigResponse)
async def update_chat_defaults(
    payload: ChatProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await provider_config.update_chat(db, payload)


@router.patch("/embeddings/defaults", response_model=EmbeddingProviderConfigResponse)
async def update_embedding_defaults(
    payload: EmbeddingProviderConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        return await provider_config.update_embeddings(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/chat/{provider}/health", response_model=ProviderHealthResponse)
async def check_chat_provider_health(
    provider: ChatProvider,
    model: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
):
    config = provider_config.chat_configs[provider]
    model_name = model or config.model
    service = AIService(
        provider=provider,
        model=model_name,
        fallback_model=config.fallback_model,
        base_url=config.base_url,
        api_key=config.api_key,
    )

    started = perf_counter()
    try:
        await service.generate_chat_response(
            messages=[
                {
                    "role": "user",
                    "content": "Health check. Reply with ok.",
                }
            ],
            model=model_name,
        )
        healthy = True
        message = "Provider responded."
    except Exception as exc:
        healthy = False
        message = str(exc)

    return ProviderHealthResponse(
        provider=provider.value,
        kind="chat",
        model=model_name,
        healthy=healthy,
        message=message,
        latency_ms=elapsed_ms(started),
    )


@router.get("/embeddings/{provider}/health", response_model=ProviderHealthResponse)
async def check_embedding_provider_health(
    provider: EmbeddingProvider,
    model: str | None = Query(default=None),
    dimensions: int | None = Query(default=None),
    _user: User = Depends(get_current_user),
):
    config = provider_config.embedding_configs[provider]
    model_name = model or config.model

    try:
        service = EmbeddingService(
            provider=provider,
            model_name=model_name,
            dimensions=dimensions if dimensions is not None else config.dimensions,
            base_url=config.base_url,
            api_key=config.api_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    started = perf_counter()
    try:
        await service.embed_text("health check")
        healthy = True
        message = "Provider responded."
    except Exception as exc:
        healthy = False
        message = str(exc)

    return ProviderHealthResponse(
        provider=provider.value,
        kind="embedding",
        model=model_name,
        healthy=healthy,
        message=message,
        latency_ms=elapsed_ms(started),
    )


def elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)
