import httpx

from app.enums import ChatProvider
from app.services.ai.providers import (
    AIProvider,
    GeminiProvider,
    GroqAIProvider,
    OllamaProvider,
    OpenRouterProvider,
)
from app.services.provider_config import provider_config


class AIService:
    def __init__(
        self,
        provider: ChatProvider | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        config = provider_config.chat

        self.provider_name = provider or config.provider
        self.model = model or config.model
        self.fallback_model = fallback_model if fallback_model is not None else config.fallback_model
        self.base_url = base_url or config.base_url
        self.api_key = api_key if api_key is not None else config.api_key

        self.provider = self._build_provider()

    def _build_provider(
        self,
    ) -> AIProvider:
        if self.provider_name == ChatProvider.OLLAMA:
            return OllamaProvider(
                base_url=self.base_url,
            )

        if self.provider_name == ChatProvider.OPENROUTER:
            return OpenRouterProvider(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        if self.provider_name == ChatProvider.GROQ:
            return GroqAIProvider(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        if self.provider_name == ChatProvider.GEMINI:
            return GeminiProvider(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        raise ValueError(f"Unsupported chat provider: {self.provider_name}")

    async def generate_chat_response(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        used_model = model or self.model

        prepared_messages = messages

        if system_prompt:
            prepared_messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                *messages,
            ]

        try:
            return await self.provider.chat(
                messages=prepared_messages,
                model=used_model,
            )

        except (httpx.HTTPError, KeyError, IndexError):
            if not self.fallback_model:
                raise

            return await self.provider.chat(
                messages=prepared_messages,
                model=self.fallback_model,
            )
