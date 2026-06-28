import httpx

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
        async with httpx.AsyncClient(timeout=120) as client:
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