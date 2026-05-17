"""Word document processing module for RAG system."""

import logging
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree


logger = logging.getLogger(__name__)


class WordProcessor:
    """Extract text and lightweight metadata from Word documents."""

    WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)

    def process_word(self, word_path: str | Path) -> dict:
        """Process a Word document and return page-like text blocks.

        Only DOCX files are supported because they are structured ZIP/XML files.
        Legacy binary DOC files need a separate converter before ingestion.
        """
        word_path = Path(word_path)
        if not word_path.exists():
            raise FileNotFoundError(f"Word file not found: {word_path}")
        if word_path.suffix.lower() != ".docx":
            raise ValueError("Only DOCX Word files are supported for RAG indexing")

        if self.verbose:
            logger.info("[Word Processing] Starting to process: %s", word_path)
            logger.info("[Word Processing] File size: %.2f KB", word_path.stat().st_size / 1024)

        text = self._extract_docx_text(word_path)
        title = word_path.stem or "Unknown"

        pages_content = [
            {
                "page_number": 1,
                "text": text,
                "length": len(text),
                "metadata": {"source_format": "docx"},
            }
        ]

        if not text:
            logger.warning("[Word Processing] No extractable text found in DOCX: %s", word_path)

        metadata = {
            "title": title,
            "author": "Unknown",
            "subject": "N/A",
            "created": "N/A",
            "modified": "N/A",
            "total_pages": 1,
        }

        return {
            "status": "success",
            "metadata": metadata,
            "pages": pages_content,
            "total_text_length": len(text),
        }

    def _extract_docx_text(self, word_path: Path) -> str:
        with zipfile.ZipFile(word_path) as docx:
            document_xml = docx.read("word/document.xml")

        root = ElementTree.fromstring(document_xml)
        paragraphs: list[str] = []

        for paragraph in root.findall(".//w:p", self.WORD_NS):
            parts: list[str] = []
            for node in paragraph.iter():
                tag = node.tag.rsplit("}", 1)[-1]
                if tag == "t" and node.text:
                    parts.append(node.text)
                elif tag == "tab":
                    parts.append("\t")
                elif tag in {"br", "cr"}:
                    parts.append("\n")

            paragraph_text = unicodedata.normalize("NFC", "".join(parts)).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)

        return "\n\n".join(paragraphs)
