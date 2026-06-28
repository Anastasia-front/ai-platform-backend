from io import BytesIO
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .base import TextExtractor


class DocxExtractor(TextExtractor):
    supported_extensions = {".docx"}

    def extract_bytes(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> str:

        try:
            with ZipFile(BytesIO(file_bytes)) as archive:
                document_xml = archive.read("word/document.xml")

        except KeyError as exc:
            raise ValueError("DOCX file is missing word/document.xml") from exc

        except BadZipFile as exc:
            raise ValueError("Invalid DOCX file") from exc

        root = ElementTree.fromstring(document_xml)

        namespace = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }

        paragraphs = []

        for paragraph in root.findall(".//w:p", namespace):
            text = "".join(
                node.text or "" for node in paragraph.findall(".//w:t", namespace)
            ).strip()

            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs)
