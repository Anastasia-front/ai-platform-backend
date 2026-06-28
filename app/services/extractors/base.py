from abc import ABC, abstractmethod
from pathlib import Path


class TextExtractor(ABC):
    supported_extensions: set[str] = set()

    def supports(
        self,
        file_path: Path,
    ) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def extract_bytes(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> str:
        """
        Extract plain text from the raw file bytes.

        Args:
            file_bytes: Raw file contents.
            filename: Original filename (used to determine format if needed).

        Returns:
            Extracted plain text.
        """
        raise NotImplementedError