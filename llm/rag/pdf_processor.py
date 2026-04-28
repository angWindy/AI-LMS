"""PDF processing module for RAG system."""

import json
import logging
import unicodedata
from pathlib import Path
from typing import Optional
import PyPDF2

try:
    import fitz as pymupdf  # PyMuPDF - better text extraction
except ImportError:
    pymupdf = None


logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDF files to extract text and metadata."""

    def __init__(self, verbose: bool = True):
        """Initialize PDF processor.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)

    @staticmethod
    def _normalize_str(value: str) -> str:
        """Normalize a string value: Unicode NFC + strip."""
        if not value:
            return value
        return unicodedata.normalize("NFC", str(value)).strip()

    def process_pdf(self, pdf_path: str | Path) -> dict:
        """Process a PDF file and extract text with metadata.
        
        Tries PyMuPDF first (better extraction quality), then falls back
        to PyPDF2.  Warns when pages yield no text (image-based PDFs).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.verbose:
            logger.info(f"[PDF Processing] Starting to process: {pdf_path}")
            logger.info(f"[PDF Processing] File size: {pdf_path.stat().st_size / 1024:.2f} KB")
        
        if pymupdf is not None:
            return self._process_with_pymupdf(pdf_path)
        return self._process_with_pypdf2(pdf_path)

    def _process_with_pymupdf(self, pdf_path: Path) -> dict:
        """Extract text using PyMuPDF (fitz)."""
        try:
            doc = pymupdf.open(str(pdf_path))
            num_pages = len(doc)

            if self.verbose:
                logger.info(f"[PDF Processing] Using PyMuPDF — total pages: {num_pages}")

            pages_content = []
            empty_pages = 0
            for page_num in range(num_pages):
                page = doc[page_num]
                text = page.get_text() or ""
                text = self._normalize_str(text)

                if not text:
                    empty_pages += 1

                if self.verbose:
                    preview = text[:100].replace('\n', ' ')
                    logger.debug(f"[PDF Processing] Page {page_num + 1}: {len(text)} chars - {preview}...")

                pages_content.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'length': len(text),
                    'metadata': {'rotation': page.rotation},
                })

            meta = doc.metadata or {}
            metadata = {
                'title': self._normalize_str(meta.get('title') or '') or 'Unknown',
                'author': self._normalize_str(meta.get('author') or '') or 'Unknown',
                'subject': self._normalize_str(meta.get('subject') or '') or 'N/A',
                'created': str(meta.get('creationDate', 'N/A')),
                'modified': str(meta.get('modDate', 'N/A')),
                'total_pages': num_pages,
            }
            doc.close()

            total_chars = sum(p['length'] for p in pages_content)
            if empty_pages == num_pages:
                logger.warning(
                    "[PDF Processing] All %d pages are empty — this PDF appears to be "
                    "image-based (scanned). OCR would be required to extract text.",
                    num_pages,
                )
            elif empty_pages > 0 and self.verbose:
                logger.warning(
                    "[PDF Processing] %d/%d pages have no extractable text.",
                    empty_pages, num_pages,
                )

            if self.verbose:
                logger.info(f"[PDF Processing] Document title: {metadata['title']}")
                logger.info(f"[PDF Processing] Total text extracted: {total_chars} characters")

            return {
                'status': 'success',
                'metadata': metadata,
                'pages': pages_content,
                'total_text_length': total_chars,
            }
        except Exception as e:
            logger.error(f"[PDF Processing] PyMuPDF failed: {e}. Falling back to PyPDF2.")
            return self._process_with_pypdf2(pdf_path)

    def _process_with_pypdf2(self, pdf_path: Path) -> dict:
        """Extract text using PyPDF2 (fallback)."""
        try:
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(reader.pages)
                
                if self.verbose:
                    logger.info(f"[PDF Processing] Using PyPDF2 — total pages: {num_pages}")
                
                pages_content = []
                empty_pages = 0
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    text = unicodedata.normalize("NFC", text)

                    if not text:
                        empty_pages += 1
                    
                    if self.verbose:
                        text_preview = text[:100].replace('\n', ' ')
                        logger.debug(f"[PDF Processing] Page {page_num}: {len(text)} chars - {text_preview}...")
                    
                    pages_content.append({
                        'page_number': page_num,
                        'text': text,
                        'length': len(text),
                        'metadata': {
                            'rotation': getattr(page, '/Rotate', 0),
                        }
                    })
                
                doc_metadata = reader.metadata or {}
                metadata = {
                    'title': self._normalize_str(doc_metadata.get('/Title', '')) or 'Unknown',
                    'author': self._normalize_str(doc_metadata.get('/Author', '')) or 'Unknown',
                    'subject': self._normalize_str(doc_metadata.get('/Subject', '')) or 'N/A',
                    'created': str(doc_metadata.get('/CreationDate', 'N/A')),
                    'modified': str(doc_metadata.get('/ModDate', 'N/A')),
                    'total_pages': num_pages,
                }

                total_chars = sum(p['length'] for p in pages_content)
                if empty_pages == num_pages:
                    logger.warning(
                        "[PDF Processing] All %d pages are empty — this PDF appears to be "
                        "image-based (scanned). OCR would be required to extract text.",
                        num_pages,
                    )
                elif empty_pages > 0 and self.verbose:
                    logger.warning(
                        "[PDF Processing] %d/%d pages have no extractable text.",
                        empty_pages, num_pages,
                    )
                
                if self.verbose:
                    logger.info(f"[PDF Processing] Document title: {metadata['title']}")
                    logger.info(f"[PDF Processing] Document author: {metadata['author']}")
                
                result = {
                    'status': 'success',
                    'metadata': metadata,
                    'pages': pages_content,
                    'total_text_length': total_chars,
                }
                
                if self.verbose:
                    logger.info(f"[PDF Processing] Total text extracted: {result['total_text_length']} characters")
                    logger.info(f"[PDF Processing] PDF processing completed successfully")
                
                return result
                
        except Exception as e:
            logger.error(f"[PDF Processing] Error processing PDF: {str(e)}")
            raise

    def extract_text_by_page(self, pdf_path: str | Path) -> list[dict]:
        """Extract text organized by pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of page dictionaries with text and metadata
        """
        result = self.process_pdf(pdf_path)
        return result['pages']

    def save_processing_result(self, result: dict, output_path: str | Path) -> None:
        """Save processing result to JSON file.
        
        Args:
            result: Processing result dictionary
            output_path: Path to save the JSON output
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            logger.info(f"[PDF Processing] Result saved to: {output_path}")
