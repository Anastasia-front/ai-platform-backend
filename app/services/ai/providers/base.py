from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ) -> str:
        raise NotImplementedError

    async def stream_chat(
        self,
        *,
        messages: list[dict],
        model: str,
    ) -> AsyncIterator[str]:
        yield await self.chat(messages=messages, model=model)
