from abc import ABC, abstractmethod
from pathlib import Path


class TextExtractor(ABC):
    supported_extensions: set[str] = set()

    def supports(
        self,
        file_path: Path,
        mime_type: str | None = None,
    ) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def extract(
        self,
        file_path: Path,
    ) -> str:
        raise NotImplementedError
