"""Hierarchical chunking module for RAG system."""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from enum import Enum


logger = logging.getLogger(__name__)


class ChunkType(str, Enum):
    """Types of chunks in hierarchical structure."""
    DOCUMENT = "document"
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


@dataclass
class Chunk:
    """Represents a chunk of text with metadata."""
    
    id: str  # Unique chunk ID
    type: ChunkType
    content: str
    page_number: int
    parent_id: Optional[str] = None
    children_ids: list[str] = None
    level: int = 0  # Hierarchy level (0=document, 1=section, etc.)
    start_char: int = 0  # Starting character position
    end_char: int = 0  # Ending character position
    tokens_count: int = 0  # Approximate token count
    embedding: Optional[list[float]] = None  # Vector embedding
    metadata: dict = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}
        if not self.tokens_count:
            self.tokens_count = self._estimate_tokens()
    
    def _estimate_tokens(self) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: ~4 characters per token
        return len(self.content) // 4
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary."""
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    def to_json(self) -> str:
        """Convert chunk to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class Document:
    """Represents a document with hierarchical chunks."""
    
    id: str
    title: str
    source_path: str
    chunks: list[Chunk] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """Convert document to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'source_path': self.source_path,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'metadata': self.metadata,
            'total_chunks': len(self.chunks),
        }
    
    def to_json(self) -> str:
        """Convert document to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class HierarchicalChunker:
    """Chunk documents hierarchically for RAG system."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        max_tokens_per_chunk: int = 300,
        verbose: bool = True,
    ):
        """Initialize hierarchical chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks in characters
            max_tokens_per_chunk: Maximum tokens per chunk (soft limit)
            verbose: Enable detailed logging
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.verbose = verbose
        self.chunk_counter = 0
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def chunk_document(self, pages: list[dict], doc_metadata: dict) -> Document:
        """Create hierarchical chunks from extracted pages.
        
        Args:
            pages: List of page dictionaries from PDF processor
            doc_metadata: Document metadata
            
        Returns:
            Document object with hierarchical chunks
        """
        doc_id = doc_metadata.get('title', 'document').lower().replace(' ', '_')
        document = Document(
            id=doc_id,
            title=doc_metadata.get('title', 'Untitled'),
            source_path=doc_metadata.get('source_path', ''),
            metadata=doc_metadata,
        )
        
        self.chunk_counter = 0
        
        if self.verbose:
            logger.info(f"[Chunking] Starting chunking process for: {document.title}")
            logger.info(f"[Chunking] Configuration: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        # Process each page
        for page_data in pages:
            page_num = page_data['page_number']
            text = page_data['text']
            
            if self.verbose:
                logger.debug(f"[Chunking] Processing page {page_num} ({len(text)} chars)")
            
            # Chunk the page text
            chunks = self._chunk_text(text, page_num, level=0)
            document.chunks.extend(chunks)
        
        if self.verbose:
            logger.info(f"[Chunking] Total chunks created: {len(document.chunks)}")
            total_tokens = sum(c.tokens_count for c in document.chunks)
            logger.info(f"[Chunking] Total tokens across chunks: {total_tokens}")
        
        return document
    
    def _chunk_text(
        self,
        text: str,
        page_num: int,
        level: int = 0,
    ) -> list[Chunk]:
        """Chunk text with overlapping windows.
        
        Args:
            text: Text to chunk
            page_num: Page number
            level: Hierarchy level
            
        Returns:
            List of chunks
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk_text = ""
        current_start_char = 0
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # If adding this paragraph would exceed chunk size
            if len(current_chunk_text) + len(paragraph) > self.chunk_size:
                # Save current chunk if not empty
                if current_chunk_text.strip():
                    chunk = self._create_chunk(
                        content=current_chunk_text.strip(),
                        page_num=page_num,
                        level=level,
                        start_char=current_start_char,
                    )
                    chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = current_chunk_text[-self.chunk_overlap:] if len(current_chunk_text) > self.chunk_overlap else ""
                current_chunk_text = overlap_text + paragraph
                current_start_char = max(0, len(current_chunk_text) - len(paragraph))
            else:
                current_chunk_text += "\n\n" + paragraph if current_chunk_text else paragraph
        
        # Add final chunk
        if current_chunk_text.strip():
            chunk = self._create_chunk(
                content=current_chunk_text.strip(),
                page_num=page_num,
                level=level,
                start_char=current_start_char,
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        page_num: int,
        level: int,
        start_char: int,
    ) -> Chunk:
        """Create a chunk object.
        
        Args:
            content: Chunk content
            page_num: Page number
            level: Hierarchy level
            start_char: Start character position
            
        Returns:
            Chunk object
        """
        self.chunk_counter += 1
        chunk_id = f"chunk_{page_num:03d}_{self.chunk_counter:04d}"
        
        # Determine chunk type based on length and content
        if len(content) < 200:
            chunk_type = ChunkType.SENTENCE
        elif len(content) < 500:
            chunk_type = ChunkType.PARAGRAPH
        else:
            chunk_type = ChunkType.SECTION
        
        chunk = Chunk(
            id=chunk_id,
            type=chunk_type,
            content=content,
            page_number=page_num,
            level=level,
            start_char=start_char,
            end_char=start_char + len(content),
        )
        
        if self.verbose:
            logger.debug(f"[Chunking] Created {chunk_type.value}: {chunk_id} ({len(content)} chars, {chunk.tokens_count} tokens)")
        
        return chunk
    
    def save_chunks(self, document: Document, output_path: str | Path) -> None:
        """Save document and chunks to JSON file.
        
        Args:
            document: Document object with chunks
            output_path: Path to save JSON output
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            'document': document.to_dict(),
            'chunk_count': len(document.chunks),
            'chunk_types': {
                ct.value: len([c for c in document.chunks if c.type == ct])
                for ct in ChunkType
            },
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            logger.info(f"[Chunking] Chunks saved to: {output_path}")
            logger.info(f"[Chunking] Chunk type distribution: {output_data['chunk_types']}")
    
    def load_chunks(self, json_path: str | Path) -> Document:
        """Load document and chunks from JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Document object
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_data = data['document']
        
        # Reconstruct chunks
        chunks = []
        for chunk_data in doc_data['chunks']:
            chunk_data['type'] = ChunkType(chunk_data['type'])
            chunks.append(Chunk(**chunk_data))
        
        document = Document(
            id=doc_data['id'],
            title=doc_data['title'],
            source_path=doc_data['source_path'],
            chunks=chunks,
            metadata=doc_data['metadata'],
        )
        
        if self.verbose:
            logger.info(f"[Chunking] Loaded {len(chunks)} chunks from: {json_path}")
        
        return document
