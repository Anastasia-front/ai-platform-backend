import httpx


class AIService:

    def __init__(
        self,
        model: str = "gemma2:2b",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    async def generate_chat_response(
        self,
        messages: list[dict],
        system_prompt: str | None = (
            "You are a helpful AI assistant "
            "inside an AI automation platform."
        ),
    ) -> str:

        system_message = {
            "role": "system",
            "content": system_prompt,
        }

        final_messages = [
            system_message,
            *messages,
        ]

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": final_messages,
                    "stream": False,
                },
                timeout=120,
            )

            response.raise_for_status()

            data = response.json()

            return data["message"]["content"]