from pathlib import Path

from .base import TextExtractor


class TxtExtractor(TextExtractor):
    supported_extensions = {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".json",
        ".log",
        ".yaml",
        ".yml",
    }

    def extract(
        self,
        file_path: Path,
    ) -> str:
        return file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
