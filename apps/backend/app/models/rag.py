"""Database models for the RAG system.

These tables mirror the LMS document hierarchy:

    Course (UUID)
      \u2514\u2500 Lesson (UUID)
           \u2514\u2500 Material (UUID)        \u2190 source artefact uploaded by Teacher
                \u2514\u2500 RAGDocument        \u2190 indexed representation in vector store
                     \u2514\u2500 RAGChunk[]    \u2190 embedded content units
"""

import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    LargeBinary,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - pgvector optional in test environments
    Vector = None
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# Default embedding dimension matches Google Gemini ``gemini-embedding-001``.
RAG_EMBEDDING_DIM = 3072


class RAGDocument(Base):
    """Indexed RAG document, optionally linked to a Course / Lesson / Material."""

    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(255), unique=True, index=True, nullable=False)

    # Hierarchy links to the existing LMS document tree.
    course_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    lesson_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    material_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )
    uploaded_by = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    source_path = Column(Text, nullable=True)
    source_type = Column(String(50), default="pdf")  # pdf, docx, txt, ...
    file_hash = Column(String(64), nullable=True)  # SHA-256 for de-dup
    metadata_json = Column("metadata", JSON, nullable=True)
    chunks_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    chunks = relationship(
        "RAGChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RAGDocument {self.doc_id}: {self.title}>"


class RAGChunk(Base):
    """Chunk of content with its vector embedding."""

    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(255), unique=True, index=True, nullable=False)
    document_id = Column(
        Integer,
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_type = Column(String(50), default="section")  # paragraph | sentence | section
    embedding_dim = Column(Integer, default=RAG_EMBEDDING_DIM)
    if Vector is not None:
        embedding = Column(Vector(RAG_EMBEDDING_DIM), nullable=True)
    else:  # pragma: no cover - SQLite/test fallback
        embedding = Column(LargeBinary, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    tokens_count = Column(Integer, default=0)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    document = relationship("RAGDocument", back_populates="chunks")
    search_results = relationship("RAGSearchResult", back_populates="chunk")

    def __repr__(self) -> str:
        return f"<RAGChunk {self.chunk_id}>"


class RAGSearchSession(Base):
    """Search session for analytics / feedback."""

    __tablename__ = "rag_search_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lesson_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query = Column(Text, nullable=False)
    query_tokens = Column(Integer, default=0)
    results_count = Column(Integer, default=0)
    search_duration_ms = Column(Integer, nullable=True)
    is_successful = Column(Integer, default=1)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), index=True)

    search_results = relationship("RAGSearchResult", back_populates="session")

    def __repr__(self) -> str:
        return f"<RAGSearchSession {self.id}: {self.query[:50]}>"


class RAGSearchResult(Base):
    """Individual ranked result from a search session."""

    __tablename__ = "rag_search_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("rag_search_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id = Column(
        String(255),
        ForeignKey("rag_chunks.chunk_id", ondelete="CASCADE"),
        nullable=False,
    )
    relevance_score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    was_selected = Column(Integer, default=0)
    user_rating = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    session = relationship("RAGSearchSession", back_populates="search_results")
    chunk = relationship("RAGChunk", back_populates="search_results")

    def __repr__(self) -> str:
        score = f"{self.relevance_score:.4f}" if self.relevance_score is not None else "N/A"
        return f"<RAGSearchResult {self.id}: {score}>"


class RAGIntegration(Base):
    """Optional explicit RAG integration with a lesson or assignment."""

    __tablename__ = "rag_integrations"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    assignment_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_id = Column(
        Integer,
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    integration_type = Column(String(50), default="reference")  # reference | required | supplementary
    usage_count = Column(Integer, default=0)
    feedback = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<RAGIntegration {self.id}>"


# Composite indexes for the most common filter combinations.
Index("idx_rag_documents_course_lesson", RAGDocument.course_id, RAGDocument.lesson_id)
Index("idx_rag_documents_active", RAGDocument.is_active)
