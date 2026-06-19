from .base import TextExtractor
from .docx import DocxExtractor
from .pdf import PdfExtractor
from .txt import TxtExtractor

DEFAULT_EXTRACTORS = (
    TxtExtractor(),
    PdfExtractor(),
    DocxExtractor(),
)

__all__ = [
    "DEFAULT_EXTRACTORS",
    "DocxExtractor",
    "PdfExtractor",
    "TextExtractor",
    "TxtExtractor",
]
