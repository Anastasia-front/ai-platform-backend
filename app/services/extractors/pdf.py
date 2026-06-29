from io import BytesIO

from .base import TextExtractor


class PdfExtractor(TextExtractor):
    supported_extensions = {".pdf"}

    def extract_bytes(
        self,
        file_bytes: bytes,
    ) -> str:

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF extraction requires pypdf") from exc

        reader = PdfReader(BytesIO(file_bytes))

        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""

            if text.strip():
                pages.append(text.strip())

        return "\n\n".join(pages)
