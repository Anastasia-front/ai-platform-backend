from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import decrypt_secret, encrypt_secret, settings
from app.enums import ChatProvider, EmbeddingProvider
from app.models import ProviderConfig
from app.schemas import (
    ChatProviderConfigResponse,
    ChatProviderConfigUpdate,
    EmbeddingProviderConfigResponse,
    EmbeddingProviderConfigUpdate,
    ProviderConfigResponse,
    ProvidersResponse,
    ProviderStatus,
)

CHAT_KIND = "chat"
EMBEDDING_KIND = "embedding"


@dataclass
class ChatProviderConfigState:
    provider: ChatProvider
    model: str
    fallback_model: str | None
    base_url: str
    api_key: str
    active: bool = False


@dataclass
class EmbeddingProviderConfigState:
    provider: EmbeddingProvider
    model: str
    dimensions: int
    base_url: str
    api_key: str
    active: bool = False


class ProviderConfigService:
    def __init__(self):
        self.chat_configs = {
            provider: ChatProviderConfigState(
                provider=provider,
                model=settings.CHAT_MODEL if provider == settings.CHAT_PROVIDER else "",
                fallback_model=(
                    settings.CHAT_FALLBACK_MODEL
                    if provider == settings.CHAT_PROVIDER
                    else None
                ),
                base_url=self._default_chat_base_url(provider),
                api_key=(
                    settings.CHAT_API_KEY if provider == settings.CHAT_PROVIDER else ""
                ),
                active=provider == settings.CHAT_PROVIDER,
            )
            for provider in ChatProvider
        }
        self.embedding_configs = {
            provider: EmbeddingProviderConfigState(
                provider=provider,
                model=(
                    settings.EMBEDDING_MODEL
                    if provider == settings.EMBEDDING_PROVIDER
                    else ""
                ),
                dimensions=settings.EMBEDDING_DIM,
                base_url=self._default_embedding_base_url(provider),
                api_key=(
                    settings.EMBEDDING_API_KEY
                    if provider == settings.EMBEDDING_PROVIDER
                    else ""
                ),
                active=provider == settings.EMBEDDING_PROVIDER,
            )
            for provider in EmbeddingProvider
        }

    @property
    def chat(self) -> ChatProviderConfigState:
        return next(config for config in self.chat_configs.values() if config.active)

    @property
    def embeddings(self) -> EmbeddingProviderConfigState:
        return next(
            config for config in self.embedding_configs.values() if config.active
        )

    async def load_from_db(self, db: AsyncSession) -> None:
        result = await db.execute(select(ProviderConfig))
        rows = result.scalars().all()

        for row in rows:
            if row.kind == CHAT_KIND:
                provider = ChatProvider(row.provider)
                self.chat_configs[provider] = ChatProviderConfigState(
                    provider=provider,
                    model=row.model,
                    fallback_model=row.fallback_model,
                    base_url=row.base_url,
                    api_key=decrypt_secret(row.encrypted_api_key),
                    active=row.active,
                )
            elif row.kind == EMBEDDING_KIND:
                provider = EmbeddingProvider(row.provider)
                self.embedding_configs[provider] = EmbeddingProviderConfigState(
                    provider=provider,
                    model=row.model,
                    dimensions=row.dimensions or settings.EMBEDDING_DIM,
                    base_url=row.base_url,
                    api_key=decrypt_secret(row.encrypted_api_key),
                    active=row.active,
                )

    async def seed_defaults(self, db: AsyncSession) -> None:
        changed = False

        for config in self.chat_configs.values():
            if not await self._get_row(db, CHAT_KIND, config.provider.value):
                db.add(self._chat_row(config))
                changed = True

        for config in self.embedding_configs.values():
            if not await self._get_row(db, EMBEDDING_KIND, config.provider.value):
                db.add(self._embedding_row(config))
                changed = True

        if changed:
            await db.commit()

    def list_providers(self) -> ProvidersResponse:
        return ProvidersResponse(
            chat=[
                ProviderStatus(
                    name=config.provider.value,
                    kind=CHAT_KIND,
                    active=config.active,
                    default_model=config.model,
                    base_url=config.base_url,
                    api_key_configured=bool(config.api_key),
                    supports_api_key=config.provider != ChatProvider.OLLAMA,
                )
                for config in self.chat_configs.values()
            ],
            embeddings=[
                ProviderStatus(
                    name=config.provider.value,
                    kind=EMBEDDING_KIND,
                    active=config.active,
                    default_model=config.model,
                    base_url=config.base_url,
                    api_key_configured=bool(config.api_key),
                    supports_api_key=config.provider != EmbeddingProvider.OLLAMA,
                )
                for config in self.embedding_configs.values()
            ],
            current=self.current_config(),
        )

    def current_config(self) -> ProviderConfigResponse:
        return ProviderConfigResponse(
            chat=ChatProviderConfigResponse(
                provider=self.chat.provider,
                model=self.chat.model,
                fallback_model=self.chat.fallback_model,
                base_url=self.chat.base_url,
                api_key_configured=bool(self.chat.api_key),
            ),
            embeddings=EmbeddingProviderConfigResponse(
                provider=self.embeddings.provider,
                model=self.embeddings.model,
                dimensions=self.embeddings.dimensions,
                base_url=self.embeddings.base_url,
                api_key_configured=bool(self.embeddings.api_key),
            ),
        )

    async def update_chat(
        self,
        db: AsyncSession,
        payload: ChatProviderConfigUpdate,
    ) -> ChatProviderConfigResponse:
        provider = payload.provider or self.chat.provider
        config = self.chat_configs[provider]

        if payload.model is not None:
            config.model = payload.model
        if payload.fallback_model is not None:
            config.fallback_model = payload.fallback_model or None
        if payload.base_url is not None:
            config.base_url = payload.base_url
        if payload.api_key is not None:
            config.api_key = payload.api_key

        for item in self.chat_configs.values():
            item.active = item.provider == provider

        await self._save_all_chat(db)
        return self.current_config().chat

    async def update_embeddings(
        self,
        db: AsyncSession,
        payload: EmbeddingProviderConfigUpdate,
    ) -> EmbeddingProviderConfigResponse:
        provider = payload.provider or self.embeddings.provider
        config = self.embedding_configs[provider]

        if payload.model is not None:
            config.model = payload.model
        if payload.dimensions is not None:
            if payload.dimensions <= 0:
                raise ValueError("dimensions must be greater than 0")
            config.dimensions = payload.dimensions
        if payload.base_url is not None:
            config.base_url = payload.base_url
        if payload.api_key is not None:
            config.api_key = payload.api_key

        for item in self.embedding_configs.values():
            item.active = item.provider == provider

        await self._save_all_embeddings(db)
        return self.current_config().embeddings

    async def _save_all_chat(self, db: AsyncSession) -> None:
        for config in self.chat_configs.values():
            row = await self._get_row(db, CHAT_KIND, config.provider.value)
            if not row:
                db.add(self._chat_row(config))
            else:
                row.model = config.model
                row.fallback_model = config.fallback_model
                row.base_url = config.base_url
                row.encrypted_api_key = encrypt_secret(config.api_key)
                row.active = config.active
                row.dimensions = None

        await db.commit()

    async def _save_all_embeddings(self, db: AsyncSession) -> None:
        for config in self.embedding_configs.values():
            row = await self._get_row(db, EMBEDDING_KIND, config.provider.value)
            if not row:
                db.add(self._embedding_row(config))
            else:
                row.model = config.model
                row.fallback_model = None
                row.base_url = config.base_url
                row.encrypted_api_key = encrypt_secret(config.api_key)
                row.active = config.active
                row.dimensions = config.dimensions

        await db.commit()

    async def _get_row(
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

    def _chat_row(self, config: ChatProviderConfigState) -> ProviderConfig:
        return ProviderConfig(
            kind=CHAT_KIND,
            provider=config.provider.value,
            model=config.model,
            fallback_model=config.fallback_model,
            base_url=config.base_url,
            encrypted_api_key=encrypt_secret(config.api_key),
            active=config.active,
            dimensions=None,
        )

    def _embedding_row(self, config: EmbeddingProviderConfigState) -> ProviderConfig:
        return ProviderConfig(
            kind=EMBEDDING_KIND,
            provider=config.provider.value,
            model=config.model,
            fallback_model=None,
            base_url=config.base_url,
            encrypted_api_key=encrypt_secret(config.api_key),
            active=config.active,
            dimensions=config.dimensions,
        )

    def _default_chat_base_url(self, provider: ChatProvider) -> str:
        defaults = {
            # ChatProvider.OLLAMA: settings.CHAT_BASE_URL,
            ChatProvider.OLLAMA: "http://localhost:11434",
            ChatProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            ChatProvider.GROQ: "https://api.groq.com/openai/v1",
            ChatProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta",
        }
        return defaults[provider]

    def _default_embedding_base_url(self, provider: EmbeddingProvider) -> str:
        defaults = {
            # EmbeddingProvider.OLLAMA: settings.EMBEDDING_BASE_URL,
            ChatProvider.OLLAMA: "http://localhost:11434",
            EmbeddingProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            EmbeddingProvider.GEMINI: "https://generativelanguage.googleapis.com/v1beta",
        }
        return defaults[provider]


provider_config = ProviderConfigService()
