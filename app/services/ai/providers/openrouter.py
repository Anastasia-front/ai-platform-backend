import httpx

from app.services.ai.providers.base import AIProvider


class OpenRouterProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]