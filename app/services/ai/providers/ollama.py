import json

import httpx

from app.core import settings
from app.services.ai.providers.base import AIProvider


class OllamaProvider(AIProvider):
    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ) -> str:
        async with httpx.AsyncClient(timeout=settings.PROVIDER_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["message"]["content"]

    async def stream_chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ):
        async with httpx.AsyncClient(timeout=settings.PROVIDER_REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
