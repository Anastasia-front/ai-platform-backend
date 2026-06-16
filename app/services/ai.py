import httpx

from app.core import settings


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
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:

        used_model = model or self.model

        ollama_messages = messages

        if system_prompt:
            ollama_messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                *messages,
            ]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": used_model,
                        "messages": ollama_messages,
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()

                data = response.json()

                return data["message"]["content"]

            except Exception:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.fallback_model,
                        "messages": ollama_messages,
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()

                data = response.json()

                return data["message"]["content"]