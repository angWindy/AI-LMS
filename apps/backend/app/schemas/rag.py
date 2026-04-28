"""Pydantic schemas for RAG API."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Request schemas
class RAGDocumentUpload(BaseModel):
    """Request to upload a document for RAG."""

    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    course_id: Optional[uuid.UUID] = None
    lesson_id: Optional[uuid.UUID] = None


class RAGSearchRequest(BaseModel):
    """Request to search using RAG (optionally scoped to a course/lesson)."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: Optional[str] = None
    course_id: Optional[uuid.UUID] = None
    lesson_id: Optional[uuid.UUID] = None


class RAGSearchFeedback(BaseModel):
    """Feedback on RAG search result."""
    
    session_id: int
    result_id: int
    rating: int = Field(..., ge=1, le=5)
    was_helpful: bool = True
    notes: Optional[str] = None


# Response schemas
class RAGChunkResponse(BaseModel):
    """Response model for a chunk."""
    
    chunk_id: str
    content: str
    page_number: Optional[int]
    chunk_type: str
    tokens_count: int
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class RAGSearchResponse(BaseModel):
    """Response to RAG search."""
    
    status: str
    query: str
    results_count: int
    results: List[RAGChunkResponse]
    execution_time_ms: Optional[float] = None
    
    class Config:
        from_attributes = True


class RAGDocumentResponse(BaseModel):
    """Response for a RAG document."""
    
    doc_id: str
    title: str
    description: Optional[str]
    source_type: str
    chunks_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RAGIngestionResponse(BaseModel):
    """Response from document ingestion."""
    
    status: str
    document_id: str
    title: str
    pages: int
    chunks: int
    total_tokens: int
    message: str
    
    class Config:
        from_attributes = True


class RAGStatsResponse(BaseModel):
    """RAG system statistics."""
    
    total_documents: int = 0
    total_chunks: int = 0
    total_tokens: int = 0
    search_count: int = 0
    avg_relevance: float = 0.0
    system_status: str = "ready"


class RAGSearchSessionResponse(BaseModel):
    """Response for search session."""
    
    session_id: int
    query: str
    results_count: int
    search_duration_ms: int
    results: List[RAGChunkResponse]
    
    class Config:
        from_attributes = True
