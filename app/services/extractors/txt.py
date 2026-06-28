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

    def extract_bytes(
        self,
        file_bytes: bytes,
    ) -> str:

        return file_bytes.decode(
            "utf-8",
            errors="replace",
        )
