"""Vector store for RAG system using PostgreSQL and pgvector."""

import json
import logging
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
    def add_chunks(self, chunks: list[Chunk], document_id: str) -> bool:
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
        host: str = "localhost",
        port: int = 5432,
        database: str = "lms",
        user: str = "postgres",
        password: str = "postgres",
        verbose: bool = True,
    ):
        """Initialize PostgreSQL vector store.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            verbose: Enable detailed logging
        """
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
                    title VARCHAR(500),
                    source_path TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chunks table with vector column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id SERIAL PRIMARY KEY,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    doc_id VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    chunk_type VARCHAR(50),
                    embedding vector(768),
                    tokens_count INTEGER,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doc_id) REFERENCES rag_documents(doc_id) ON DELETE CASCADE
                );
            """)
            
            # Create index for faster similarity search
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding 
                ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
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
            
            # Add document
            cursor.execute("""
                INSERT INTO rag_documents (doc_id, title, source_path, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                document.id,
                document.title,
                document.source_path,
                Json(document.metadata),
            ))
            
            if self.verbose:
                logger.info(f"[VectorStore] Added document: {document.id}")
            
            # Add chunks
            for chunk in chunks:
                # Convert embedding to pgvector format
                embedding_str = None
                if chunk.embedding:
                    # Convert list to vector string format
                    embedding_str = '[' + ','.join(str(x) for x in chunk.embedding) + ']'
                
                cursor.execute("""
                    INSERT INTO rag_chunks 
                    (chunk_id, doc_id, content, page_number, chunk_type, embedding, tokens_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP;
                """, (
                    chunk.id,
                    document.id,
                    chunk.content,
                    chunk.page_number,
                    chunk.type.value,
                    embedding_str,
                    chunk.tokens_count,
                    Json(chunk.metadata),
                ))
            
            self.connection.commit()
            
            if self.verbose:
                logger.info(f"[VectorStore] Added {len(chunks)} chunks for document {document.id}")
            
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
            
            # Build query
            where_clause = ""
            params = [embedding_str, top_k]
            
            if doc_id:
                where_clause = "WHERE doc_id = %s"
                params.insert(1, doc_id)
            
            query = f"""
                SELECT 
                    id,
                    chunk_id,
                    doc_id,
                    content,
                    page_number,
                    chunk_type,
                    (1 - (embedding <=> %s::vector)) as similarity,
                    metadata
                FROM rag_chunks
                {where_clause}
                ORDER BY embedding <=> %s::vector
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
                LEFT JOIN rag_chunks c ON d.doc_id = c.doc_id
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
        
        for chunk in chunks:
            self.chunks.append({
                'chunk_id': chunk.id,
                'doc_id': document.id,
                'content': chunk.content,
                'page_number': chunk.page_number,
                'type': chunk.type.value,
                'embedding': chunk.embedding,
                'metadata': chunk.metadata,
            })
        
        if self.verbose:
            logger.info(f"[VectorStore] Added {len(chunks)} chunks to in-memory store")
        
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
                
                similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
                
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
