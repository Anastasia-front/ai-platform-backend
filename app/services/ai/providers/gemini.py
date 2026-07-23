import json

import httpx

from app.core import settings
from app.services.ai.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ) -> str:
        contents = [
            {
                "role": "user" if message["role"] != "assistant" else "model",
                "parts": [
                    {
                        "text": message["content"],
                    }
                ],
            }
            for message in messages
            if message["role"] != "system"
        ]

        system_instruction = None

        system_messages = [
            message["content"]
            for message in messages
            if message["role"] == "system"
        ]

        if system_messages:
            system_instruction = {
                "parts": [
                    {
                        "text": "\n\n".join(system_messages),
                    }
                ]
            }

        payload = {
            "contents": contents,
        }

        if system_instruction:
            payload["system_instruction"] = system_instruction

        async with httpx.AsyncClient(timeout=settings.PROVIDER_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent",
                params={
                    "key": self.api_key,
                },
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def stream_chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ):
        contents = [
            {
                "role": "user" if message["role"] != "assistant" else "model",
                "parts": [
                    {
                        "text": message["content"],
                    }
                ],
            }
            for message in messages
            if message["role"] != "system"
        ]

        system_messages = [
            message["content"]
            for message in messages
            if message["role"] == "system"
        ]

        payload = {
            "contents": contents,
        }

        if system_messages:
            payload["system_instruction"] = {
                "parts": [
                    {
                        "text": "\n\n".join(system_messages),
                    }
                ]
            }

        async with httpx.AsyncClient(timeout=settings.PROVIDER_REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/models/{model}:streamGenerateContent",
                params={
                    "key": self.api_key,
                    "alt": "sse",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = json.loads(line.removeprefix("data:").strip())
                    for candidate in data.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            text = part.get("text", "")
                            if text:
                                yield text
