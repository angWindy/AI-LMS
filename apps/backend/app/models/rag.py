"""Database models for RAG system."""

from sqlalchemy import Column, String, Integer, Text, Float, DateTime, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


class RAGDocument(Base):
    """Document metadata for RAG system."""
    
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(255), unique=True, index=True, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source_path = Column(Text, nullable=True)
    source_type = Column(String(50), default="pdf")  # pdf, txt, web, etc.
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    metadata = Column(JSON, nullable=True)
    chunks_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RAGDocument {self.doc_id}: {self.title}>"


class RAGChunk(Base):
    """Chunk of content from RAG documents."""
    
    __tablename__ = "rag_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(Integer, ForeignKey("rag_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_type = Column(String(50), default="section")  # section, paragraph, sentence, etc.
    embedding_dim = Column(Integer, default=768)
    # Note: For actual vector storage, use pgvector directly or separate vector DB
    metadata = Column(JSON, nullable=True)
    tokens_count = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("RAGDocument", back_populates="chunks")
    search_results = relationship("RAGSearchResult", back_populates="chunk")
    
    def __repr__(self):
        return f"<RAGChunk {self.chunk_id}>"


class RAGSearchSession(Base):
    """Track RAG search sessions for analytics."""
    
    __tablename__ = "rag_search_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    query = Column(Text, nullable=False)
    query_tokens = Column(Integer, default=0)
    results_count = Column(Integer, default=0)
    search_duration_ms = Column(Integer, nullable=True)
    is_successful = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    search_results = relationship("RAGSearchResult", back_populates="session")
    
    def __repr__(self):
        return f"<RAGSearchSession {self.id}: {self.query[:50]}>"


class RAGSearchResult(Base):
    """Individual search results from RAG."""
    
    __tablename__ = "rag_search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("rag_search_sessions.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("rag_chunks.id"), nullable=False)
    relevance_score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)  # Position in results (1, 2, 3, ...)
    was_selected = Column(Integer, default=0)  # Did user click on this result?
    user_rating = Column(Integer, nullable=True)  # User feedback (1-5 stars)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    session = relationship("RAGSearchSession", back_populates="search_results")
    chunk = relationship("RAGChunk", back_populates="search_results")
    
    def __repr__(self):
        return f"<RAGSearchResult {self.id}: {self.relevance_score:.4f}>"


class RAGIntegration(Base):
    """Track RAG integration with lessons/assignments."""
    
    __tablename__ = "rag_integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("rag_documents.id"), nullable=False)
    integration_type = Column(String(50), default="reference")  # reference, required, supplementary
    usage_count = Column(Integer, default=0)
    feedback = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RAGIntegration {self.id}>"
