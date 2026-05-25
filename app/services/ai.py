import httpx
from app.core.config import settings


class AIService:
    def __init__(
        self,
        model: str = settings.OLLAMA_MODEL,
        fallback_model: str = settings.OLLAMA_FALLBACK_MODEL,
        base_url: str = settings.OLLAMA_BASE_URL,
    ):
        self.model = model
        self.fallback_model = fallback_model
        self.base_url = base_url

    async def generate_chat_response(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> str:

        used_model = model or self.model

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": used_model,
                        "messages": messages,
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]

            except Exception:
                # fallback model attempt
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.fallback_model,
                        "messages": messages,
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]