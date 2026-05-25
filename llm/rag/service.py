"""RAG Service for LMS - High-level RAG operations."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict

from llm.rag.pdf_processor import PDFProcessor
from llm.rag.word_processor import WordProcessor
from llm.rag.chunker import HierarchicalChunker, Document
from llm.rag.embedder import EmbeddingService
from llm.rag.vector_store import VectorStore, InMemoryVectorStore, PostgresVectorStore


logger = logging.getLogger(__name__)


class RAGService:
    """High-level RAG service for LMS integration."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        use_postgres: bool = False,
        verbose: bool = True,
        initialize_schema: bool = True,
    ):
        """Initialize RAG service.
        
        Args:
            vector_store: Custom vector store instance
            embedding_service: Custom embedding service instance
            use_postgres: Use PostgreSQL vector store
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.initialize_schema = initialize_schema
        if verbose:
            logger.setLevel(logging.INFO)
        
        # Initialize embedding service
        if embedding_service:
            self.embedding_service = embedding_service
        else:
            try:
                self.embedding_service = EmbeddingService(verbose=verbose)
                logger.info("[RAGService] Initialized Gemini embedding service")
            except ValueError as e:
                logger.warning(f"[RAGService] Embedding service unavailable: {e}")
                self.embedding_service = None

        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
        elif use_postgres:
            try:
                embedding_dim = (
                    self.embedding_service.embedding_dimension
                    if self.embedding_service
                    else 768
                )
                self.vector_store = PostgresVectorStore(
                    embedding_dimension=embedding_dim,
                    verbose=verbose,
                    initialize_schema=initialize_schema,
                )
                logger.info("[RAGService] Using PostgreSQL vector store")
            except Exception as e:
                logger.warning(f"[RAGService] Failed to connect to PostgreSQL: {e}")
                logger.info("[RAGService] Falling back to in-memory vector store")
                self.vector_store = InMemoryVectorStore(verbose=verbose)
        else:
            self.vector_store = InMemoryVectorStore(verbose=verbose)
            logger.info("[RAGService] Using in-memory vector store")
    
    def ingest_pdf(
        self,
        pdf_path: str | Path,
        document_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        material_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        file_hash: Optional[str] = None,
        title: Optional[str] = None,
        extra_metadata: Optional[Dict] = None,
    ) -> Dict:
        # Tiện ích nhập PDF vào RAG (tự map sang ingest_document).
        """Ingest a PDF file into the RAG system.

        Args:
            pdf_path: Path to PDF file.
            document_id: Optional explicit ``doc_id`` (auto-derived otherwise).
            course_id, lesson_id, material_id, uploaded_by:
                Hierarchy links (UUID strings) persisted with the document.
            file_hash: Optional SHA-256 of the raw file for de-duplication.
            title: Optional override for the document title.
            extra_metadata: Free-form metadata merged into the document record.
        """
        return self.ingest_document(
            file_path=pdf_path,
            document_id=document_id,
            course_id=course_id,
            lesson_id=lesson_id,
            material_id=material_id,
            uploaded_by=uploaded_by,
            file_hash=file_hash,
            title=title,
            extra_metadata=extra_metadata,
        )

    def ingest_document(
        self,
        file_path: str | Path,
        document_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        material_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        file_hash: Optional[str] = None,
        title: Optional[str] = None,
        extra_metadata: Optional[Dict] = None,
    ) -> Dict:
        # Đọc file, chunk, embed và lưu vào vector store.
        """Ingest a supported document into RAG.

        Text is extracted first, then chunked, then embedded. This keeps the
        embedding calls scoped to retrieval-ready chunks instead of raw files.
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if self.verbose:
            logger.info("[RAGService] Starting document ingestion: %s", file_path)

        try:
            if suffix == ".pdf":
                source_type = "pdf"
                processed_result = PDFProcessor(verbose=self.verbose).process_pdf(file_path)
            elif suffix == ".docx":
                source_type = "docx"
                processed_result = WordProcessor(verbose=self.verbose).process_word(file_path)
            else:
                raise ValueError(f"Unsupported RAG document type: {suffix or 'unknown'}")

            doc_metadata = {
                **processed_result['metadata'],
                'source_path': str(file_path),
            }
            for key, value in {
                "course_id": str(course_id) if course_id else None,
                "lesson_id": str(lesson_id) if lesson_id else None,
                "material_id": str(material_id) if material_id else None,
                "uploaded_by": str(uploaded_by) if uploaded_by else None,
                "file_hash": file_hash,
                "source_type": source_type,
            }.items():
                if value is not None:
                    doc_metadata[key] = value
            if extra_metadata:
                doc_metadata.update(extra_metadata)

            chunker = HierarchicalChunker(verbose=self.verbose)
            document = chunker.chunk_document(
                pages=processed_result['pages'],
                doc_metadata=doc_metadata,
            )

            if not document_id:
                document_id = file_path.stem.lower().replace(' ', '_')
            document.id = document_id
            if title:
                document.title = title
            self._namespace_chunk_ids(document)

            if self.embedding_service:
                document = self.embedding_service.embed_document(document)

            self.vector_store.add_chunks(document.chunks, document)

            result = {
                'status': 'success',
                'document_id': document.id,
                'title': document.title,
                'pages': processed_result['metadata'].get('total_pages', len(processed_result['pages'])),
                'chunks': len(document.chunks),
                'total_tokens': sum(c.tokens_count for c in document.chunks),
                'course_id': doc_metadata.get('course_id'),
                'lesson_id': doc_metadata.get('lesson_id'),
                'material_id': doc_metadata.get('material_id'),
                'source_type': source_type,
                'message': f'Successfully ingested {len(document.chunks)} chunks from {file_path.name}',
            }

            if self.verbose:
                logger.info("[RAGService] Document ingestion completed: %s", result)

            return result

        except Exception as e:
            logger.error("[RAGService] Document ingestion failed: %s", str(e))
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to ingest document: {str(e)}',
            }

    def _namespace_chunk_ids(self, document: Document) -> None:
        # Gắn namespace vào chunk_id để tránh trùng giữa các tài liệu.
        """Make chunk IDs unique per document while preserving hierarchy links."""
        id_map: dict[str, str] = {}
        for chunk in document.chunks:
            old_id = chunk.id
            candidate = f"{document.id}:{old_id}"
            if len(candidate) > 255:
                digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()
                candidate = f"{document.id}:{digest}"
            id_map[old_id] = candidate

        for chunk in document.chunks:
            chunk.id = id_map[chunk.id]
            if chunk.parent_id:
                chunk.parent_id = id_map.get(chunk.parent_id, chunk.parent_id)
            chunk.children_ids = [id_map.get(child_id, child_id) for child_id in chunk.children_ids]
            if chunk.metadata:
                if chunk.metadata.get("parent_id"):
                    chunk.metadata["parent_id"] = id_map.get(chunk.metadata["parent_id"], chunk.metadata["parent_id"])
                if chunk.metadata.get("children_ids"):
                    chunk.metadata["children_ids"] = [
                        id_map.get(child_id, child_id)
                        for child_id in chunk.metadata["children_ids"]
                    ]
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        course_id: Optional[str] = None,
        lesson_id: Optional[str] = None,
        course_only: bool = False,
    ) -> Dict:
        """Search for relevant chunks using RAG, optionally scoped to a course/lesson."""
        if self.verbose:
            logger.info(
                "[RAGService] Searching: %s... (top_k=%s, course=%s, lesson=%s, course_only=%s)",
                query[:100], top_k, course_id, lesson_id, course_only,
            )

        try:
            if self.embedding_service:
                query_embedding = self.embedding_service.embed_query(query)
            else:
                logger.warning("[RAGService] No embedding service available")
                query_embedding = [0.0] * 3072

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                doc_id=document_id,
                course_id=course_id,
                lesson_id=lesson_id,
                course_only=course_only,
            )

            formatted_results = [
                {
                    'chunk_id': r['chunk_id'],
                    'content': r['content'],
                    'page_number': r.get('page_number', 0),
                    'relevance': r.get('similarity', r.get('score', 0)),
                    'document_id': r.get('doc_id', document_id),
                    'course_id': r.get('course_id'),
                    'lesson_id': r.get('lesson_id'),
                    'material_id': r.get('material_id'),
                    'document_title': r.get('document_title'),
                }
                for r in results
            ]

            return {
                'status': 'success',
                'query': query,
                'results_count': len(formatted_results),
                'results': formatted_results,
            }

        except Exception as e:
            logger.error(f"[RAGService] Search failed: {str(e)}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'results': [],
            }

    def delete_by_material(self, material_id: str) -> Dict:
        """Remove every RAG document linked to a Material."""
        try:
            count = self.vector_store.delete_by_material(str(material_id))
            return {'status': 'success', 'material_id': str(material_id), 'deleted': count}
        except Exception as e:
            logger.error(f"[RAGService] delete_by_material failed: {e}")
            return {'status': 'error', 'material_id': str(material_id), 'error': str(e)}

    def delete_by_lesson(self, lesson_id: str) -> Dict:
        try:
            count = self.vector_store.delete_by_lesson(str(lesson_id))
            return {'status': 'success', 'lesson_id': str(lesson_id), 'deleted': count}
        except Exception as e:
            logger.error(f"[RAGService] delete_by_lesson failed: {e}")
            return {'status': 'error', 'lesson_id': str(lesson_id), 'error': str(e)}

    def delete_by_course(self, course_id: str) -> Dict:
        try:
            count = self.vector_store.delete_by_course(str(course_id))
            return {'status': 'success', 'course_id': str(course_id), 'deleted': count}
        except Exception as e:
            logger.error(f"[RAGService] delete_by_course failed: {e}")
            return {'status': 'error', 'course_id': str(course_id), 'error': str(e)}
    
    def get_document_chunks(self, document_id: str) -> Dict:
        """Get all chunks for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document chunks
        """
        try:
            # This is a simplified version - in production, you'd query the database
            return {
                'status': 'success',
                'document_id': document_id,
                'message': f'Retrieved chunks for document {document_id}',
            }
        except Exception as e:
            logger.error(f"[RAGService] Failed to get document chunks: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def delete_document(self, document_id: str) -> Dict:
        """Delete document from RAG system.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Result dictionary
        """
        if self.verbose:
            logger.info(f"[RAGService] Deleting document: {document_id}")
        
        try:
            success = self.vector_store.delete_document(document_id)
            
            if success:
                return {
                    'status': 'success',
                    'document_id': document_id,
                    'message': f'Document {document_id} deleted',
                }
            else:
                return {
                    'status': 'error',
                    'document_id': document_id,
                    'error': 'Document not found or already deleted',
                }
                
        except Exception as e:
            logger.error(f"[RAGService] Delete failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
            }
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics.
        
        Returns:
            Dictionary with system stats
        """
        return {
            'vector_store_type': type(self.vector_store).__name__,
            'embedding_service': 'Gemini' if self.embedding_service else 'None',
            'status': 'ready',
        }


# Singleton instance for LMS integration
_rag_service: Optional[RAGService] = None


def get_rag_service(
    use_postgres: bool = False,
    verbose: bool = True,
    initialize_schema: bool = True,
) -> RAGService:
    """Get or create RAG service instance.
    
    Args:
        use_postgres: Use PostgreSQL vector store
        verbose: Enable detailed logging
        initialize_schema: Run vector-store schema initialization.
        
    Returns:
        RAGService instance
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService(
            use_postgres=use_postgres,
            verbose=verbose,
            initialize_schema=initialize_schema,
        )
    
    return _rag_service


def reset_rag_service():
    """Reset RAG service instance."""
    global _rag_service
    _rag_service = None
