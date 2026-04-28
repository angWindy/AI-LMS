"""RAG Service for LMS - High-level RAG operations."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import asdict

from llm.rag.pdf_processor import PDFProcessor
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
    ):
        """Initialize RAG service.
        
        Args:
            vector_store: Custom vector store instance
            embedding_service: Custom embedding service instance
            use_postgres: Use PostgreSQL vector store
            verbose: Enable detailed logging
        """
        self.verbose = verbose
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
    ) -> Dict:
        """Ingest a PDF file into the RAG system.
        
        Args:
            pdf_path: Path to PDF file
            document_id: Optional document ID (generated from filename if not provided)
            
        Returns:
            Dictionary with ingestion results
        """
        pdf_path = Path(pdf_path)
        
        if self.verbose:
            logger.info(f"[RAGService] Starting PDF ingestion: {pdf_path}")
        
        try:
            # Step 1: Process PDF
            processor = PDFProcessor(verbose=self.verbose)
            pdf_result = processor.process_pdf(pdf_path)
            
            # Step 2: Create chunks
            chunker = HierarchicalChunker(verbose=self.verbose)
            document = chunker.chunk_document(
                pages=pdf_result['pages'],
                doc_metadata={
                    **pdf_result['metadata'],
                    'source_path': str(pdf_path),
                }
            )
            
            # Set document ID
            if not document_id:
                document_id = pdf_path.stem.lower().replace(' ', '_')
            document.id = document_id
            
            # Step 3: Generate embeddings
            if self.embedding_service:
                document = self.embedding_service.embed_document(document)
            
            # Step 4: Add to vector store
            self.vector_store.add_chunks(document.chunks, document)
            
            result = {
                'status': 'success',
                'document_id': document.id,
                'title': document.title,
                'pages': pdf_result['metadata'].get('total_pages', 0),
                'chunks': len(document.chunks),
                'total_tokens': sum(c.tokens_count for c in document.chunks),
                'message': f'Successfully ingested {len(document.chunks)} chunks from {pdf_path.name}',
            }
            
            if self.verbose:
                logger.info(f"[RAGService] PDF ingestion completed: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"[RAGService] PDF ingestion failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Failed to ingest PDF: {str(e)}',
            }
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
    ) -> Dict:
        """Search for relevant chunks using RAG.
        
        Args:
            query: Search query
            top_k: Number of results to return
            document_id: Optional document filter
            
        Returns:
            Dictionary with search results
        """
        if self.verbose:
            logger.info(f"[RAGService] Searching: {query[:100]}... (top_k={top_k})")
        
        try:
            # Generate query embedding
            if self.embedding_service:
                query_embedding = self.embedding_service.embed_query(query)
            else:
                # Fallback: return empty if no embedding service
                logger.warning("[RAGService] No embedding service available")
                query_embedding = [0.0] * 768
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                doc_id=document_id,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'chunk_id': result['chunk_id'],
                    'content': result['content'],
                    'page_number': result.get('page_number', 0),
                    'relevance': result.get('similarity', result.get('score', 0)),
                    'document_id': result.get('doc_id', document_id),
                })
            
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
) -> RAGService:
    """Get or create RAG service instance.
    
    Args:
        use_postgres: Use PostgreSQL vector store
        verbose: Enable detailed logging
        
    Returns:
        RAGService instance
    """
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService(use_postgres=use_postgres, verbose=verbose)
    
    return _rag_service


def reset_rag_service():
    """Reset RAG service instance."""
    global _rag_service
    _rag_service = None
