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
        doc_id = self._safe_doc_id(doc_metadata)
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
        
        # Create document root chunk
        doc_chunk = Chunk(
            id=f"doc_{doc_id}",
            type=ChunkType.DOCUMENT,
            content=document.title or doc_id,
            page_number=0,
            level=0,
        )
        doc_chunk.metadata["is_structural"] = True
        document.chunks.append(doc_chunk)

        # Process each page as a section
        for page_data in pages:
            page_num = page_data['page_number']
            raw_text = page_data['text'] or ""
            text = self._normalize_text(raw_text)

            if self.verbose:
                logger.debug(f"[Chunking] Processing page {page_num} ({len(text)} chars)")

            if not text:
                if self.verbose:
                    logger.debug(f"[Chunking] Page {page_num} has no text \u2014 skipping (image-based?)")
                continue

            section_id = f"section_{page_num:03d}"
            section_chunk = Chunk(
                id=section_id,
                type=ChunkType.SECTION,
                content=text,
                page_number=page_num,
                level=1,
                parent_id=doc_chunk.id,
            )
            section_chunk.metadata["is_structural"] = True

            # Chunk the page text into paragraph/sentence chunks
            chunks = self._chunk_text(
                text,
                page_num,
                level=2,
                parent_id=section_id,
            )
            section_chunk.children_ids = [chunk.id for chunk in chunks]
            doc_chunk.children_ids.append(section_id)

            document.chunks.append(section_chunk)
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
        parent_id: Optional[str] = None,
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
        
        paragraphs = self._split_paragraphs(text)
        cursor = 0

        for paragraph in paragraphs:
            for piece in self._split_long_text(paragraph):
                start_char = text.find(piece, cursor)
                if start_char < 0:
                    start_char = cursor
                chunk = self._create_chunk(
                    content=piece,
                    page_num=page_num,
                    level=level,
                    start_char=start_char,
                    parent_id=parent_id,
                )
                chunks.append(chunk)
                cursor = start_char + len(piece)
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        page_num: int,
        level: int,
        start_char: int,
        parent_id: Optional[str] = None,
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
        
        # Determine chunk type based on level and length
        if level >= 2:
            if len(content) < 200:
                chunk_type = ChunkType.SENTENCE
            else:
                chunk_type = ChunkType.PARAGRAPH
        else:
            if len(content) < 500:
                chunk_type = ChunkType.PARAGRAPH
            else:
                chunk_type = ChunkType.SECTION
        
        chunk = Chunk(
            id=chunk_id,
            type=chunk_type,
            content=content,
            page_number=page_num,
            parent_id=parent_id,
            level=level,
            start_char=start_char,
            end_char=start_char + len(content),
        )
        chunk.metadata.update(
            {
                "parent_id": parent_id,
                "level": level,
            }
        )
        
        if self.verbose:
            logger.debug(f"[Chunking] Created {chunk_type.value}: {chunk_id} ({len(content)} chars, {chunk.tokens_count} tokens)")
        
        return chunk

    def _safe_doc_id(self, doc_metadata: dict) -> str:
        title = (doc_metadata.get("title") or "").strip().lower()
        source_path = (doc_metadata.get("source_path") or "").strip().lower()
        base = title or Path(source_path).stem or "document"
        return re.sub(r"[^a-z0-9_\-]+", "_", base).strip("_") or "document"

    def _normalize_text(self, text: str) -> str:
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"(?<=\w)-\n(?=\w)", "", cleaned)
        cleaned = re.sub(r"(?<!\n)\n(?!\n)", " ", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _split_paragraphs(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs and text.strip():
            return [text.strip()]
        return paragraphs

    def _split_long_text(self, text: str) -> list[str]:
        max_chars = min(self.chunk_size, self.max_tokens_per_chunk * 4)
        if len(text) <= max_chars:
            return [text]

        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) == 1:
            return self._split_by_window(text, max_chars)

        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if not sentence.strip():
                continue
            if len(current) + len(sentence) + 1 > max_chars:
                if current:
                    chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current.strip())
        return chunks

    def _split_by_window(self, text: str, max_chars: int) -> list[str]:
        if max_chars <= 0:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + max_chars)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = max(0, end - self.chunk_overlap)
        return chunks
    
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
