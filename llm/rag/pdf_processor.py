"""PDF processing module for RAG system."""

import json
import logging
from pathlib import Path
from typing import Optional
import PyPDF2


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

    def process_pdf(self, pdf_path: str | Path) -> dict:
        """Process a PDF file and extract text with metadata.
        
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
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(reader.pages)
                
                if self.verbose:
                    logger.info(f"[PDF Processing] Total pages: {num_pages}")
                
                # Extract text and metadata from each page
                pages_content = []
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    
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
                
                # Extract document metadata
                doc_metadata = reader.metadata or {}
                metadata = {
                    'title': doc_metadata.get('/Title', 'Unknown'),
                    'author': doc_metadata.get('/Author', 'Unknown'),
                    'subject': doc_metadata.get('/Subject', 'N/A'),
                    'created': str(doc_metadata.get('/CreationDate', 'N/A')),
                    'modified': str(doc_metadata.get('/ModDate', 'N/A')),
                    'total_pages': num_pages,
                }
                
                if self.verbose:
                    logger.info(f"[PDF Processing] Document title: {metadata['title']}")
                    logger.info(f"[PDF Processing] Document author: {metadata['author']}")
                
                result = {
                    'status': 'success',
                    'metadata': metadata,
                    'pages': pages_content,
                    'total_text_length': sum(p['length'] for p in pages_content),
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
