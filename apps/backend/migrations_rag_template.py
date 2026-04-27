"""
Alembic migration for RAG system - Template

Run from apps/backend directory:
    alembic revision --autogenerate -m "Add RAG models"
    alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# This is a template - Alembic will auto-generate the actual migration

def upgrade():
    # Create rag_documents table
    op.create_table(
        'rag_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.String(255), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_path', sa.Text(), nullable=True),
        sa.Column('source_type', sa.String(50), server_default='pdf'),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('chunks_count', sa.Integer(), server_default='0'),
        sa.Column('total_tokens', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_id'),
    )
    op.create_index('ix_rag_documents_doc_id', 'rag_documents', ['doc_id'])
    
    # Create rag_chunks table
    op.create_table(
        'rag_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.String(255), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('chunk_type', sa.String(50), server_default='section'),
        sa.Column('embedding_dim', sa.Integer(), server_default='768'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_count', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['document_id'], ['rag_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chunk_id'),
    )
    op.create_index('ix_rag_chunks_chunk_id', 'rag_chunks', ['chunk_id'])
    
    # Create rag_search_sessions table
    op.create_table(
        'rag_search_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('query_tokens', sa.Integer(), server_default='0'),
        sa.Column('results_count', sa.Integer(), server_default='0'),
        sa.Column('search_duration_ms', sa.Integer(), nullable=True),
        sa.Column('is_successful', sa.Integer(), server_default='1'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rag_search_sessions_created_at', 'rag_search_sessions', ['created_at'])
    
    # Create rag_search_results table
    op.create_table(
        'rag_search_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('was_selected', sa.Integer(), server_default='0'),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['chunk_id'], ['rag_chunks.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['rag_search_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create rag_integrations table
    op.create_table(
        'rag_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=True),
        sa.Column('assignment_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('integration_type', sa.String(50), server_default='reference'),
        sa.Column('usage_count', sa.Integer(), server_default='0'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['rag_documents.id'], ),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('rag_integrations')
    op.drop_table('rag_search_results')
    op.drop_table('rag_search_sessions')
    op.drop_table('rag_chunks')
    op.drop_table('rag_documents')
