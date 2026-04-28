"""Vector store for RAG system using PostgreSQL and pgvector."""

import json
import logging
import os
from typing import Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

from llm.rag.chunker import Chunk, Document


logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_chunks(self, chunks: list[Chunk], document: Document) -> bool:
        """Add chunks to the vector store."""
        pass
    
    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Search for similar chunks."""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        pass


class PostgresVectorStore(VectorStore):
    """Vector store using PostgreSQL and pgvector extension."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        embedding_dimension: int = 768,
        verbose: bool = True,
    ):
        """Initialize PostgreSQL vector store.
        
        Args:
            host: Database host (defaults to DB_HOST env var, then 'localhost')
            port: Database port (defaults to DB_PORT env var, then 5432)
            database: Database name (defaults to DB_NAME env var, then 'lms_db')
            user: Database user (defaults to DB_USER env var, then 'postgres')
            password: Database password (defaults to DB_PASSWORD env var, then 'postgres')
            verbose: Enable detailed logging
        """
        host = host or os.getenv("DB_HOST", "localhost")
        port = port or int(os.getenv("DB_PORT", "5432"))
        database = database or os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "lms_db"))
        user = user or os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
        password = password or os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
        self.verbose = verbose
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
        }
        
        self.embedding_dimension = embedding_dimension
        self.connection = None
        
        if self.verbose:
            logger.info(f"[VectorStore] Initializing PostgreSQL vector store at {host}:{port}/{database}")
        
        self.connect()
        self.init_tables()
    
    def connect(self) -> None:
        """Connect to PostgreSQL database."""
        if psycopg2 is None:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        
        try:
            self.connection = psycopg2.connect(**self.config)
            if self.verbose:
                logger.info("[VectorStore] Connected to PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Connection failed: {str(e)}")
            raise
    
    def init_tables(self) -> None:
        """Initialize vector storage tables."""
        try:
            cursor = self.connection.cursor()
            
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            if self.verbose:
                logger.debug("[VectorStore] pgvector extension enabled")
            
            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id SERIAL PRIMARY KEY,
                    doc_id VARCHAR(255) UNIQUE NOT NULL,
                    course_id INTEGER,
                    title VARCHAR(500),
                    description TEXT,
                    source_path TEXT,
                    source_type VARCHAR(50) DEFAULT 'pdf',
                    file_hash VARCHAR(64),
                    metadata JSONB,
                    chunks_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chunks table with vector column
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    document_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    chunk_type VARCHAR(50),
                    embedding vector({self.embedding_dimension}),
                    embedding_dim INTEGER DEFAULT {self.embedding_dimension},
                    tokens_count INTEGER DEFAULT 0,
                    metadata JSONB,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
                );
            """)
            
            # Ensure required columns exist for legacy tables
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS chunks_count INTEGER DEFAULT 0;")
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS total_tokens INTEGER DEFAULT 0;")
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            cursor.execute("ALTER TABLE rag_chunks ADD COLUMN IF NOT EXISTS embedding_dim INTEGER DEFAULT %s;", (self.embedding_dimension,))
            cursor.execute("ALTER TABLE rag_chunks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            # Create HNSW index for faster similarity search (partial: only non-NULL embeddings)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding
                ON rag_chunks USING hnsw (embedding vector_cosine_ops)
                WHERE embedding IS NOT NULL;
            """)
            
            self.connection.commit()
            
            if self.verbose:
                logger.info("[VectorStore] Tables initialized successfully")
                
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error initializing tables: {str(e)}")
            self.connection.rollback()
            raise
    
    def add_chunks(self, chunks: list[Chunk], document: Document) -> bool:
        """Add chunks to the vector store.
        
        Args:
            chunks: List of chunks to add
            document: Document metadata
            
        Returns:
            True if successful
        """
        try:
            cursor = self.connection.cursor()
            
            total_tokens = sum(chunk.tokens_count for chunk in chunks)
            cursor.execute("""
                INSERT INTO rag_documents
                    (doc_id, title, source_path, metadata, chunks_count, total_tokens)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    source_path = EXCLUDED.source_path,
                    metadata = EXCLUDED.metadata,
                    chunks_count = EXCLUDED.chunks_count,
                    total_tokens = EXCLUDED.total_tokens,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """, (
                document.id,
                document.title,
                document.source_path,
                Json(document.metadata),
                len(chunks),
                total_tokens,
            ))
            document_row = cursor.fetchone()
            if not document_row:
                raise ValueError("Failed to resolve rag_documents.id for doc_id")
            document_db_id = document_row[0]
            
            if self.verbose:
                logger.info(f"[VectorStore] Added document: {document.id}")
            
            # Add chunks
            inserted_chunks = 0
            for chunk in chunks:
                if chunk.metadata.get("is_structural"):
                    continue
                embedding_str = None
                embedding_dim = None
                if chunk.embedding:
                    if len(chunk.embedding) != self.embedding_dimension:
                        logger.warning(
                            "[VectorStore] Skipping chunk %s: embedding dimension mismatch (got %s, expected %s)",
                            chunk.id,
                            len(chunk.embedding),
                            self.embedding_dimension,
                        )
                        continue
                    embedding_dim = len(chunk.embedding)
                    embedding_str = '[' + ','.join(str(x) for x in chunk.embedding) + ']'

                chunk_metadata = dict(chunk.metadata or {})
                chunk_metadata.update(
                    {
                        "parent_id": chunk.parent_id,
                        "children_ids": chunk.children_ids,
                        "level": chunk.level,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                    }
                )

                cursor.execute("""
                    INSERT INTO rag_chunks
                        (chunk_id, document_id, content, page_number, chunk_type, embedding, embedding_dim, tokens_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        content = EXCLUDED.content,
                        page_number = EXCLUDED.page_number,
                        chunk_type = EXCLUDED.chunk_type,
                        embedding = EXCLUDED.embedding,
                        embedding_dim = EXCLUDED.embedding_dim,
                        tokens_count = EXCLUDED.tokens_count,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    chunk.id,
                    document_db_id,
                    chunk.content,
                    chunk.page_number,
                    chunk.type.value,
                    embedding_str,
                    embedding_dim or self.embedding_dimension,
                    chunk.tokens_count,
                    Json(chunk_metadata),
                ))
                inserted_chunks += 1
            
            self.connection.commit()
            
            if self.verbose:
                logger.info(
                    "[VectorStore] Added %s/%s chunks for document %s",
                    inserted_chunks,
                    len(chunks),
                    document.id,
                )
            
            return True
            
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error adding chunks: {str(e)}")
            self.connection.rollback()
            return False
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
    ) -> list[dict]:
        """Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            doc_id: Optional document ID to search within
            
        Returns:
            List of search results with chunks and similarity scores
        """
        try:
            cursor = self.connection.cursor()
            
            # Convert embedding to pgvector format
            embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
            
            conditions = ["c.embedding IS NOT NULL", "d.is_active = 1"]
            params: list[object] = [embedding_str]

            if doc_id:
                conditions.append("d.doc_id = %s")
                params.append(doc_id)

            where_clause = "WHERE " + " AND ".join(conditions)
            params.extend([embedding_str, top_k])

            query = f"""
                SELECT
                    c.id,
                    c.chunk_id,
                    d.doc_id,
                    c.content,
                    c.page_number,
                    c.chunk_type,
                    (1 - (c.embedding <=> %s::vector)) as similarity,
                    c.metadata
                FROM rag_chunks c
                JOIN rag_documents d ON d.id = c.document_id
                {where_clause}
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s;
            """

            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            search_results = []
            for row in results:
                search_results.append({
                    'id': row[0],
                    'chunk_id': row[1],
                    'doc_id': row[2],
                    'content': row[3],
                    'page_number': row[4],
                    'chunk_type': row[5],
                    'similarity': float(row[6]),
                    'metadata': row[7],
                })
            
            if self.verbose:
                logger.info(f"[VectorStore] Search returned {len(search_results)} results")
                for result in search_results[:3]:
                    logger.debug(f"[VectorStore] - {result['chunk_id']}: similarity={result['similarity']:.4f}")
            
            return search_results
            
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Search error: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks and document from vector store.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            cursor = self.connection.cursor()
            
            # Delete document (cascades to chunks)
            cursor.execute("""
                DELETE FROM rag_documents WHERE doc_id = %s;
            """, (document_id,))
            
            self.connection.commit()
            
            if self.verbose:
                logger.info(f"[VectorStore] Deleted document and chunks: {document_id}")
            
            return True
            
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error deleting document: {str(e)}")
            self.connection.rollback()
            return False
    
    def get_document_stats(self, doc_id: str) -> dict:
        """Get statistics for a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with document statistics
        """
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT 
                    d.title,
                    COUNT(c.id) as chunk_count,
                    SUM(c.tokens_count) as total_tokens,
                    MIN(c.created_at) as first_created,
                    MAX(c.updated_at) as last_updated
                FROM rag_documents d
                LEFT JOIN rag_chunks c ON d.id = c.document_id
                WHERE d.doc_id = %s
                GROUP BY d.title;
            """, (doc_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'title': result[0],
                    'chunk_count': result[1] or 0,
                    'total_tokens': result[2] or 0,
                    'first_created': str(result[3]),
                    'last_updated': str(result[4]),
                }
            
            return {}
            
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error getting stats: {str(e)}")
            return {}
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            if self.verbose:
                logger.info("[VectorStore] Database connection closed")


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for testing (without database)."""
    
    def __init__(self, verbose: bool = True):
        """Initialize in-memory vector store.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.documents: dict[str, dict] = {}
        self.chunks: list[dict] = []
        
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.info("[VectorStore] Initialized in-memory vector store")
    
    def add_chunks(self, chunks: list[Chunk], document: Document) -> bool:
        """Add chunks to in-memory store.
        
        Args:
            chunks: List of chunks
            document: Document metadata
            
        Returns:
            True if successful
        """
        self.documents[document.id] = {
            'id': document.id,
            'title': document.title,
            'source_path': document.source_path,
            'metadata': document.metadata,
        }
        
        inserted_chunks = 0
        for chunk in chunks:
            if chunk.metadata.get("is_structural"):
                continue
            self.chunks.append({
                'chunk_id': chunk.id,
                'doc_id': document.id,
                'content': chunk.content,
                'page_number': chunk.page_number,
                'type': chunk.type.value,
                'embedding': chunk.embedding,
                'metadata': chunk.metadata,
            })
            inserted_chunks += 1
        
        if self.verbose:
            logger.info(
                "[VectorStore] Added %s/%s chunks to in-memory store",
                inserted_chunks,
                len(chunks),
            )
        
        return True
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
    ) -> list[dict]:
        """Search in-memory chunks.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results
            doc_id: Optional document filter
            
        Returns:
            Search results
        """
        import numpy as np
        
        results = []
        
        for chunk_data in self.chunks:
            if doc_id and chunk_data['doc_id'] != doc_id:
                continue
            
            if chunk_data['embedding']:
                vec1 = np.array(query_embedding)
                vec2 = np.array(chunk_data['embedding'])

                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    similarity = 0.0
                else:
                    similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))

                results.append({
                    'chunk_id': chunk_data['chunk_id'],
                    'doc_id': chunk_data['doc_id'],
                    'content': chunk_data['content'],
                    'page_number': chunk_data['page_number'],
                    'similarity': float(max(0.0, similarity)),
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from in-memory store.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if successful
        """
        if document_id in self.documents:
            del self.documents[document_id]
            self.chunks = [c for c in self.chunks if c['doc_id'] != document_id]
            return True
        return False
