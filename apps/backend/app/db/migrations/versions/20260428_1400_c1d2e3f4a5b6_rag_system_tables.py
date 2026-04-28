"""RAG system tables (course/lesson/material aware, 3072-dim Gemini embeddings)

Revision ID: c1d2e3f4a5b6
Revises: b7f2c1c9a001
Create Date: 2026-04-28 14:00:00.000000

This migration creates the persistent tables backing the RAG pipeline:

* ``rag_documents``       \u2013 metadata for an indexed document, linked back to
                              the LMS Course/Lesson/Material that produced it
* ``rag_chunks``          \u2013 chunk text + ``vector(3072)`` embedding (pgvector)
* ``rag_search_sessions`` \u2013 user-issued queries, scoped to course/lesson
* ``rag_search_results``  \u2013 ranked chunks returned per session
* ``rag_integrations``    \u2013 explicit attachments to lessons / assignments

If a previous (legacy) revision created these tables with INTEGER course_id /
768-dim embeddings, the migration drops and recreates the affected tables. The
RAG store is a derived index, so dropping it is non-destructive.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b7f2c1c9a001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RAG_TABLES = [
    "rag_search_results",
    "rag_search_sessions",
    "rag_integrations",
    "rag_chunks",
    "rag_documents",
]
RAG_EMBEDDING_DIM = 3072
PGVECTOR_INDEX_MAX_DIM = 2000


def upgrade() -> None:
    bind = op.get_bind()

    # Required for the vector(...) column type below.
    bind.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector;")

    # If a legacy version of these tables exists (e.g. created by an older
    # vector_store.py with INTEGER FKs / 768 dims), wipe them so we can recreate
    # with the correct schema. The RAG store is rebuildable from source files.
    for table in RAG_TABLES:
        bind.exec_driver_sql(f"DROP TABLE IF EXISTS {table} CASCADE;")

    # ---- rag_documents ---------------------------------------------------
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doc_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("course_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lesson_id", UUID(as_uuid=True), nullable=True),
        sa.Column("material_id", UUID(as_uuid=True), nullable=True, unique=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=50), server_default="pdf"),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("chunks_count", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_rag_documents_doc_id", "rag_documents", ["doc_id"])
    op.create_index("ix_rag_documents_course_id", "rag_documents", ["course_id"])
    op.create_index("ix_rag_documents_lesson_id", "rag_documents", ["lesson_id"])
    op.create_index("ix_rag_documents_material_id", "rag_documents", ["material_id"])
    op.create_index("idx_rag_documents_course_lesson", "rag_documents", ["course_id", "lesson_id"])
    op.create_index("idx_rag_documents_active", "rag_documents", ["is_active"])

    # ---- rag_chunks (with pgvector(3072) column) -------------------------
    bind.exec_driver_sql(
        """
        CREATE TABLE rag_chunks (
            id SERIAL PRIMARY KEY,
            chunk_id VARCHAR(255) UNIQUE NOT NULL,
            document_id INTEGER NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            page_number INTEGER,
            chunk_type VARCHAR(50) DEFAULT 'section',
            embedding_dim INTEGER DEFAULT 3072,
            embedding vector(3072),
            metadata JSONB,
            tokens_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    op.create_index("ix_rag_chunks_chunk_id", "rag_chunks", ["chunk_id"])
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    # pgvector approximate indexes currently support up to 2000 dimensions for
    # vector columns. Gemini embeddings are 3072d, so keep exact-scan search
    # unless a lower-dimensional projection/halfvec strategy is added later.
    if RAG_EMBEDDING_DIM <= PGVECTOR_INDEX_MAX_DIM:
        bind.exec_driver_sql(
            """
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding
            ON rag_chunks USING hnsw (embedding vector_cosine_ops)
            WHERE embedding IS NOT NULL;
            """
        )

    # ---- rag_search_sessions --------------------------------------------
    op.create_table(
        "rag_search_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lesson_id", UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("query_tokens", sa.Integer(), server_default="0"),
        sa.Column("results_count", sa.Integer(), server_default="0"),
        sa.Column("search_duration_ms", sa.Integer(), nullable=True),
        sa.Column("is_successful", sa.Integer(), server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_rag_search_sessions_user_id", "rag_search_sessions", ["user_id"])
    op.create_index("ix_rag_search_sessions_course_id", "rag_search_sessions", ["course_id"])
    op.create_index("ix_rag_search_sessions_lesson_id", "rag_search_sessions", ["lesson_id"])
    op.create_index("ix_rag_search_sessions_created_at", "rag_search_sessions", ["created_at"])

    # ---- rag_search_results ---------------------------------------------
    op.create_table(
        "rag_search_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(length=255), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("was_selected", sa.Integer(), server_default="0"),
        sa.Column("user_rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["rag_search_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["rag_chunks.chunk_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rag_search_results_session_id", "rag_search_results", ["session_id"])

    # ---- rag_integrations -----------------------------------------------
    op.create_table(
        "rag_integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", UUID(as_uuid=True), nullable=True),
        sa.Column("assignment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("integration_type", sa.String(length=50), server_default="reference"),
        sa.Column("usage_count", sa.Integer(), server_default="0"),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["rag_documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rag_integrations_lesson_id", "rag_integrations", ["lesson_id"])
    op.create_index("ix_rag_integrations_assignment_id", "rag_integrations", ["assignment_id"])
    op.create_index("ix_rag_integrations_document_id", "rag_integrations", ["document_id"])


def downgrade() -> None:
    bind = op.get_bind()
    for table in RAG_TABLES:
        bind.exec_driver_sql(f"DROP TABLE IF EXISTS {table} CASCADE;")
