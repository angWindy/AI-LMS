"""Vector store for RAG system using PostgreSQL and pgvector."""

import json
import logging
import os
from typing import Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
from urllib.parse import unquote, urlparse

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

from llm.rag.chunker import Chunk, Document


logger = logging.getLogger(__name__)

PGVECTOR_INDEX_MAX_DIM = 2000


def _parse_database_url(database_url: str | None) -> dict[str, Any]:
    """Parse a SQLAlchemy-style PostgreSQL URL into psycopg2 kwargs."""
    if not database_url:
        return {}

    parsed = urlparse(database_url)
    if not parsed.scheme.startswith("postgresql"):
        return {}

    return {
        "host": parsed.hostname,
        "port": parsed.port,
        "database": parsed.path.lstrip("/") or None,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else None,
    }


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk], document: Document) -> bool:
        """Add chunks to the vector store."""

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        course_only: bool = False,
    ) -> list[dict]:
        """Search for similar chunks (optionally scoped to a course/lesson/document)."""

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""

    def delete_by_material(self, material_id: str) -> int:
        """Delete all RAG documents linked to a Material. Returns # deleted."""
        return 0

    def delete_by_lesson(self, lesson_id: str) -> int:
        """Delete all RAG documents linked to a Lesson. Returns # deleted."""
        return 0

    def delete_by_course(self, course_id: str) -> int:
        """Delete all RAG documents linked to a Course. Returns # deleted."""
        return 0

    def is_empty(self) -> bool:  # pragma: no cover - small helper
        return True


class PostgresVectorStore(VectorStore):
    """Vector store using PostgreSQL and pgvector extension."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        embedding_dimension: int = 3072,
        verbose: bool = True,
        initialize_schema: bool = True,
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
        database_url_config = _parse_database_url(os.getenv("DATABASE_URL"))
        host = host or os.getenv("DB_HOST") or database_url_config.get("host") or "localhost"
        port = port or int(os.getenv("DB_PORT") or database_url_config.get("port") or 5432)
        database = (
            database
            or os.getenv("DB_NAME")
            or os.getenv("POSTGRES_DB")
            or database_url_config.get("database")
            or "lms_db"
        )
        user = (
            user
            or os.getenv("DB_USER")
            or os.getenv("POSTGRES_USER")
            or database_url_config.get("user")
            or "postgres"
        )
        password = (
            password
            or os.getenv("DB_PASSWORD")
            or os.getenv("POSTGRES_PASSWORD")
            or database_url_config.get("password")
            or "postgres"
        )
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
        self.initialize_schema = initialize_schema
        
        if self.verbose:
            logger.info(f"[VectorStore] Initializing PostgreSQL vector store at {host}:{port}/{database}")
        
        self.connect()
        if self.initialize_schema:
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
            cursor.execute("SET LOCAL lock_timeout = '5s';")
            cursor.execute("SET LOCAL statement_timeout = '30s';")
            
            # Enable pgvector extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            if self.verbose:
                logger.debug("[VectorStore] pgvector extension enabled")
            
            # Create documents table (UUID FKs to mirror LMS hierarchy)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rag_documents (
                    id SERIAL PRIMARY KEY,
                    doc_id VARCHAR(255) UNIQUE NOT NULL,
                    course_id UUID,
                    lesson_id UUID,
                    material_id UUID UNIQUE,
                    uploaded_by UUID,
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

            # Drop legacy integer course_id column if it exists (pre-v0.4 schema).
            cursor.execute("""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'rag_documents'
                          AND column_name = 'course_id'
                          AND data_type = 'integer'
                    ) THEN
                        ALTER TABLE rag_documents DROP COLUMN course_id;
                    END IF;
                END $$;
            """)

            # Forward-compatible columns for installs that pre-date the hierarchy fields.
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS course_id UUID;")
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS lesson_id UUID;")
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS material_id UUID;")
            cursor.execute("ALTER TABLE rag_documents ADD COLUMN IF NOT EXISTS uploaded_by UUID;")
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_documents_material_id
                ON rag_documents (material_id) WHERE material_id IS NOT NULL;
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_documents_course_id ON rag_documents (course_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_documents_lesson_id ON rag_documents (lesson_id);")
            
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

            # pgvector approximate indexes currently support up to 2000
            # dimensions for vector columns. Gemini embeddings are 3072d, so
            # keep exact-scan search unless a projection/halfvec strategy is
            # added later.
            if self.embedding_dimension <= PGVECTOR_INDEX_MAX_DIM:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding
                    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
                    WHERE embedding IS NOT NULL;
                """)
            elif self.verbose:
                logger.info(
                    "[VectorStore] Skipping HNSW index for %sd embeddings; pgvector index limit is %s",
                    self.embedding_dimension,
                    PGVECTOR_INDEX_MAX_DIM,
                )
            
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
            doc_meta = document.metadata or {}
            cursor.execute("""
                INSERT INTO rag_documents
                    (doc_id, title, source_path, metadata, chunks_count, total_tokens,
                     course_id, lesson_id, material_id, uploaded_by, source_type, file_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doc_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    source_path = EXCLUDED.source_path,
                    metadata = EXCLUDED.metadata,
                    chunks_count = EXCLUDED.chunks_count,
                    total_tokens = EXCLUDED.total_tokens,
                    course_id = COALESCE(EXCLUDED.course_id, rag_documents.course_id),
                    lesson_id = COALESCE(EXCLUDED.lesson_id, rag_documents.lesson_id),
                    material_id = COALESCE(EXCLUDED.material_id, rag_documents.material_id),
                    uploaded_by = COALESCE(EXCLUDED.uploaded_by, rag_documents.uploaded_by),
                    source_type = COALESCE(EXCLUDED.source_type, rag_documents.source_type),
                    file_hash = COALESCE(EXCLUDED.file_hash, rag_documents.file_hash),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """, (
                document.id,
                document.title,
                document.source_path,
                Json(doc_meta),
                len(chunks),
                total_tokens,
                doc_meta.get("course_id"),
                doc_meta.get("lesson_id"),
                doc_meta.get("material_id"),
                doc_meta.get("uploaded_by"),
                doc_meta.get("source_type") or "pdf",
                doc_meta.get("file_hash"),
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
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        course_only: bool = False,
    ) -> list[dict]:
        """Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            doc_id: Restrict to a single RAG document
            course_id: Restrict to documents of a specific course
            lesson_id: Restrict to documents of a specific lesson
            course_only: Restrict to course-level documents (lesson_id IS NULL)
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
            if course_id:
                conditions.append("d.course_id = %s::uuid")
                params.append(str(course_id))
            if lesson_id:
                conditions.append("d.lesson_id = %s::uuid")
                params.append(str(lesson_id))
            if course_only:
                conditions.append("d.lesson_id IS NULL")

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
                    c.metadata,
                    d.course_id,
                    d.lesson_id,
                    d.material_id,
                    d.title
                FROM rag_chunks c
                JOIN rag_documents d ON d.id = c.document_id
                {where_clause}
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s;
            """

            cursor.execute(query, params)
            results = cursor.fetchall()
            self.connection.commit()

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
                    'course_id': str(row[8]) if row[8] else None,
                    'lesson_id': str(row[9]) if row[9] else None,
                    'material_id': str(row[10]) if row[10] else None,
                    'document_title': row[11],
                })
            
            if self.verbose:
                logger.info(f"[VectorStore] Search returned {len(search_results)} results")
                for result in search_results[:3]:
                    logger.debug(f"[VectorStore] - {result['chunk_id']}: similarity={result['similarity']:.4f}")
            
            return search_results
            
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Search error: {str(e)}")
            self.connection.rollback()
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document (and chunks via FK cascade)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM rag_documents WHERE doc_id = %s;",
                (document_id,),
            )
            self.connection.commit()
            if self.verbose:
                logger.info(f"[VectorStore] Deleted document: {document_id}")
            return True
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error deleting document: {str(e)}")
            self.connection.rollback()
            return False

    def _delete_by(self, column: str, value: str) -> int:
        """Helper: delete documents where a UUID column equals ``value``."""
        if not value:
            return 0
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                f"DELETE FROM rag_documents WHERE {column} = %s::uuid RETURNING doc_id;",
                (str(value),),
            )
            deleted = cursor.fetchall() or []
            self.connection.commit()
            if self.verbose and deleted:
                logger.info(
                    "[VectorStore] Deleted %s document(s) by %s=%s",
                    len(deleted), column, value,
                )
            return len(deleted)
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] Error deleting by {column}: {str(e)}")
            self.connection.rollback()
            return 0

    def delete_by_material(self, material_id: str) -> int:
        return self._delete_by("material_id", material_id)

    def delete_by_lesson(self, lesson_id: str) -> int:
        return self._delete_by("lesson_id", lesson_id)

    def delete_by_course(self, course_id: str) -> int:
        return self._delete_by("course_id", course_id)

    def find_doc_id_by_material(self, material_id: str) -> Optional[str]:
        """Return the ``doc_id`` for a given ``material_id``, if indexed."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT doc_id FROM rag_documents WHERE material_id = %s::uuid LIMIT 1;",
                (str(material_id),),
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except psycopg2.Error as e:
            logger.error(f"[VectorStore] find_doc_id_by_material error: {e}")
            return None

    def is_empty(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM rag_chunks WHERE embedding IS NOT NULL LIMIT 1;")
            return (cursor.fetchone() or [0])[0] == 0
        except psycopg2.Error:
            return True
    
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
        meta = document.metadata or {}
        self.documents[document.id] = {
            'id': document.id,
            'title': document.title,
            'source_path': document.source_path,
            'metadata': meta,
            'course_id': str(meta.get("course_id")) if meta.get("course_id") else None,
            'lesson_id': str(meta.get("lesson_id")) if meta.get("lesson_id") else None,
            'material_id': str(meta.get("material_id")) if meta.get("material_id") else None,
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
                inserted_chunks, len(chunks),
            )
        return True

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        doc_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        course_only: bool = False,
    ) -> list[dict]:
        import numpy as np

        results = []
        course_id = str(course_id) if course_id else None
        lesson_id = str(lesson_id) if lesson_id else None

        for chunk_data in self.chunks:
            doc = self.documents.get(chunk_data['doc_id'], {})
            if doc_id and chunk_data['doc_id'] != doc_id:
                continue
            if course_id and doc.get('course_id') != course_id:
                continue
            if lesson_id and doc.get('lesson_id') != lesson_id:
                continue
            if course_only and doc.get('lesson_id') is not None:
                continue

            if chunk_data['embedding']:
                vec1 = np.array(query_embedding)
                vec2 = np.array(chunk_data['embedding'])
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                similarity = (
                    0.0 if norm1 == 0 or norm2 == 0
                    else float(np.dot(vec1, vec2) / (norm1 * norm2))
                )
                results.append({
                    'chunk_id': chunk_data['chunk_id'],
                    'doc_id': chunk_data['doc_id'],
                    'content': chunk_data['content'],
                    'page_number': chunk_data['page_number'],
                    'similarity': float(max(0.0, similarity)),
                    'course_id': doc.get('course_id'),
                    'lesson_id': doc.get('lesson_id'),
                    'material_id': doc.get('material_id'),
                    'document_title': doc.get('title'),
                })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    def delete_document(self, document_id: str) -> bool:
        if document_id in self.documents:
            del self.documents[document_id]
            self.chunks = [c for c in self.chunks if c['doc_id'] != document_id]
            return True
        return False

    def _delete_where(self, key: str, value: str) -> int:
        if not value:
            return 0
        value = str(value)
        targets = [doc_id for doc_id, doc in self.documents.items() if doc.get(key) == value]
        for doc_id in targets:
            self.delete_document(doc_id)
        return len(targets)

    def delete_by_material(self, material_id: str) -> int:
        return self._delete_where("material_id", material_id)

    def delete_by_lesson(self, lesson_id: str) -> int:
        return self._delete_where("lesson_id", lesson_id)

    def delete_by_course(self, course_id: str) -> int:
        return self._delete_where("course_id", course_id)

    def find_doc_id_by_material(self, material_id: str) -> Optional[str]:
        if not material_id:
            return None
        material_id = str(material_id)
        for doc_id, doc in self.documents.items():
            if doc.get("material_id") == material_id:
                return doc_id
        return None

    def is_empty(self) -> bool:
        return not self.chunks
