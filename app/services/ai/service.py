import httpx

from app.core import settings
from app.enums import LLMProvider
from app.services.ai.providers import (
    AIProvider,
    GeminiProvider,
    GroqAIProvider,
    OllamaProvider,
    OpenRouterProvider,
)


class AIService:
    def __init__(
        self,
        provider: LLMProvider = settings.CHAT_PROVIDER,
        model: str = settings.CHAT_MODEL,
        fallback_model: str | None = settings.CHAT_FALLBACK_MODEL,
        base_url: str = settings.CHAT_BASE_URL,
        api_key: str = settings.CHAT_API_KEY,
    ):
        self.provider_name = provider
        self.model = model
        self.fallback_model = fallback_model
        self.base_url = base_url
        self.api_key = api_key

        self.provider = self._build_provider()

    def _build_provider(
        self,
    ) -> AIProvider:
        if self.provider_name == LLMProvider.OLLAMA:
            return OllamaProvider(
                base_url=self.base_url,
            )

        if self.provider_name == LLMProvider.OPENROUTER:
            return OpenRouterProvider(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        if self.provider_name == LLMProvider.GROQ:
            return GroqAIProvider(
                api_key=self.api_key,
                base_url=self.base_url,
            )

        if self.provider_name == LLMProvider.GEMINI:
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
