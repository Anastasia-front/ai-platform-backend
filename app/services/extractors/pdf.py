from pathlib import Path

from .base import TextExtractor


class PdfExtractor(TextExtractor):
    supported_extensions = {".pdf"}

    def extract(
        self,
        file_path: Path,
    ) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "PDF extraction requires the optional 'pypdf' package"
            ) from exc

        reader = PdfReader(str(file_path))
        pages: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text() or ""

            if page_text.strip():
                pages.append(page_text.strip())

        return "\n\n".join(pages)
