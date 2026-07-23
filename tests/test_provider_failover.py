from types import SimpleNamespace

import httpx
import pytest

from app.enums import ChatProvider
from app.services.ai import service as ai_service_module
from app.services.ai.service import AIService


class FakeProvider:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc

    async def chat(self, *, messages, model):
        if self.exc:
            raise self.exc
        return self.result


def _status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://provider.example/chat")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("provider failed", request=request, response=response)


@pytest.mark.asyncio
async def test_chat_failover_uses_next_retryable_provider(monkeypatch):
    configs = [
        SimpleNamespace(provider=ChatProvider.GEMINI, model="gemini-model", api_key="k", base_url="https://gemini"),
        SimpleNamespace(provider=ChatProvider.GROQ, model="groq-model", api_key="k", base_url="https://groq"),
    ]
    providers = {
        ChatProvider.GEMINI: FakeProvider(exc=_status_error(429)),
        ChatProvider.GROQ: FakeProvider(result="groq answer"),
    }

    monkeypatch.setattr(ai_service_module.provider_config, "chat_chain", lambda fixed_provider=None: configs)
    monkeypatch.setattr(
        AIService,
        "_build_provider_for_config",
        lambda self, config: providers[config.provider],
    )

    service = AIService()

    assert await service.generate_chat_response([{"role": "user", "content": "hi"}]) == "groq answer"
    assert service.last_provider_used == "groq"
    assert service.last_model_used == "groq-model"
    assert service.last_fallback_used is True


@pytest.mark.asyncio
async def test_fixed_chat_provider_does_not_fail_over(monkeypatch):
    configs = [
        SimpleNamespace(provider=ChatProvider.GROQ, model="groq-model", api_key="k", base_url="https://groq"),
    ]

    monkeypatch.setattr(ai_service_module.provider_config, "chat_chain", lambda fixed_provider=None: configs)
    monkeypatch.setattr(
        AIService,
        "_build_provider_for_config",
        lambda self, config: FakeProvider(exc=_status_error(429)),
    )

    service = AIService(
        provider=ChatProvider.GROQ,
        model="groq-model",
        api_key="k",
        base_url="https://groq",
    )

    with pytest.raises(Exception):
        await service.generate_chat_response([{"role": "user", "content": "hi"}])
