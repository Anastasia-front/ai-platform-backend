from pydantic import BaseModel, ConfigDict

from app.enums import ChatProvider, EmbeddingProvider


class ChatProviderConfigUpdate(BaseModel):
    provider: ChatProvider | None = None
    model: str | None = None
    fallback_model: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class EmbeddingProviderConfigUpdate(BaseModel):
    provider: EmbeddingProvider | None = None
    model: str | None = None
    dimensions: int | None = None
    base_url: str | None = None
    api_key: str | None = None


class ProviderStatus(BaseModel):
    name: str
    kind: str
    active: bool
    default_model: str
    base_url: str
    api_key_configured: bool
    supports_api_key: bool
    supports_health_check: bool = True


class ChatProviderConfigResponse(BaseModel):
    provider: ChatProvider
    model: str
    fallback_model: str | None = None
    base_url: str
    api_key_configured: bool


class EmbeddingProviderConfigResponse(BaseModel):
    provider: EmbeddingProvider
    model: str
    dimensions: int
    base_url: str
    api_key_configured: bool


class ProviderConfigResponse(BaseModel):
    chat: ChatProviderConfigResponse
    embeddings: EmbeddingProviderConfigResponse


class ProvidersResponse(BaseModel):
    chat: list[ProviderStatus]
    embeddings: list[ProviderStatus]
    current: ProviderConfigResponse


class ProviderHealthResponse(BaseModel):
    provider: str
    kind: str
    model: str
    healthy: bool
    message: str
    latency_ms: int

    model_config = ConfigDict(from_attributes=True)
