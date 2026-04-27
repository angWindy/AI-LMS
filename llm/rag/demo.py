#!/usr/bin/env python3
"""
Complete RAG system demonstration and test script.

This script demonstrates the full RAG pipeline:
1. PDF Processing
2. Hierarchical Chunking
3. Embedding Generation
4. Vector Store Integration
5. RAG Retrieval
"""

import json
import sys
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RAG components
from llm.rag.pdf_processor import PDFProcessor
from llm.rag.chunker import HierarchicalChunker
from llm.rag.embedder import EmbeddingService
from llm.rag.vector_store import InMemoryVectorStore, PostgresVectorStore


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_pdf_processing(pdf_path: str | Path) -> dict:
    """Demonstrate PDF processing.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Processed PDF data
    """
    print_section("PHASE 1: PDF PROCESSING")
    
    processor = PDFProcessor(verbose=True)
    result = processor.process_pdf(pdf_path)
    
    print(f"\n✓ PDF Processing completed")
    print(f"  - Pages: {result['metadata']['total_pages']}")
    print(f"  - Total text: {result['total_text_length']} characters")
    print(f"  - Document: {result['metadata']['title']}")
    
    return result


def demo_chunking(pdf_result: dict, output_dir: str | Path = "rag_output") -> tuple:
    """Demonstrate hierarchical chunking.
    
    Args:
        pdf_result: Result from PDF processing
        output_dir: Directory to save chunking results
        
    Returns:
        Tuple of (document, chunked_json_path)
    """
    print_section("PHASE 2: HIERARCHICAL CHUNKING")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    chunker = HierarchicalChunker(
        chunk_size=1000,
        chunk_overlap=100,
        max_tokens_per_chunk=300,
        verbose=True,
    )
    
    document = chunker.chunk_document(
        pages=pdf_result['pages'],
        doc_metadata={
            **pdf_result['metadata'],
            'source_path': str(Path(__file__).parent / 'pdf_sample.pdf'),
        }
    )
    
    # Save chunks
    chunks_output = output_dir / "chunks.json"
    chunker.save_chunks(document, chunks_output)
    
    print(f"\n✓ Chunking completed")
    print(f"  - Total chunks: {len(document.chunks)}")
    chunk_types = {}
    for chunk in document.chunks:
        chunk_types[chunk.type.value] = chunk_types.get(chunk.type.value, 0) + 1
    print(f"  - Chunk types: {chunk_types}")
    print(f"  - Chunks saved to: {chunks_output}")
    
    # Print sample chunks
    print(f"\n  Sample chunks:")
    for i, chunk in enumerate(document.chunks[:3], 1):
        preview = chunk.content[:150].replace('\n', ' ')
        print(f"    [{i}] {chunk.id} ({chunk.type.value})")
        print(f"        Preview: {preview}...")
        print(f"        Length: {len(chunk.content)} chars, {chunk.tokens_count} tokens")
    
    return document, chunks_output


def demo_embedding(document, vector_store_type: str = "memory") -> tuple:
    """Demonstrate embedding generation.
    
    Args:
        document: Document with chunks
        vector_store_type: Type of vector store ("memory" or "postgres")
        
    Returns:
        Tuple of (embedded_document, vector_store)
    """
    print_section("PHASE 3: EMBEDDING GENERATION")
    
    try:
        embedding_service = EmbeddingService(
            model='gemini-embedding-001',
            verbose=True,
        )
    except ValueError as e:
        print(f"⚠ Warning: {e}")
        print(f"  Using mock embeddings (zeros) for demonstration")
        
        # Create mock embeddings
        class MockEmbeddingService:
            def __init__(self):
                self.embedding_dimension = 768
                self.verbose = True
            
            def embed_chunks(self, chunks, task_type="RETRIEVAL_DOCUMENT"):
                for chunk in chunks:
                    chunk.embedding = [0.0] * self.embedding_dimension
                logger.info(f"[Embedding] Created mock embeddings for {len(chunks)} chunks")
                return chunks
            
            def embed_query(self, query):
                return [0.0] * self.embedding_dimension
        
        embedding_service = MockEmbeddingService()
    
    # Embed chunks
    embedded_document = document
    if hasattr(embedding_service, 'embed_chunks'):
        embedded_document.chunks = embedding_service.embed_chunks(document.chunks)
    
    print(f"\n✓ Embedding completed")
    print(f"  - Total chunks embedded: {len(embedded_document.chunks)}")
    print(f"  - Embedding dimension: {embedding_service.embedding_dimension}")
    
    # Initialize vector store
    if vector_store_type == "memory":
        vector_store = InMemoryVectorStore(verbose=True)
        print(f"\n✓ Using in-memory vector store for testing")
    else:
        try:
            vector_store = PostgresVectorStore(
                host="localhost",
                port=5432,
                database="lms",
                user="postgres",
                password="postgres",
                verbose=True,
            )
            print(f"\n✓ Connected to PostgreSQL vector store")
        except Exception as e:
            print(f"⚠ PostgreSQL connection failed: {e}")
            print(f"  Falling back to in-memory store")
            vector_store = InMemoryVectorStore(verbose=True)
    
    # Add chunks to vector store
    vector_store.add_chunks(embedded_document.chunks, embedded_document)
    
    return embedded_document, vector_store, embedding_service


def demo_rag_retrieval(
    vector_store,
    embedding_service,
    query: str = "What is the main topic of this document?",
    top_k: int = 3,
):
    """Demonstrate RAG retrieval.
    
    Args:
        vector_store: Vector store instance
        embedding_service: Embedding service instance
        query: Query string
        top_k: Number of results to return
    """
    print_section("PHASE 4: RAG RETRIEVAL")
    
    print(f"Query: {query}\n")
    
    # Get query embedding
    if hasattr(embedding_service, 'embed_query'):
        query_embedding = embedding_service.embed_query(query)
    else:
        query_embedding = [0.0] * 768  # Mock
    
    # Search vector store
    results = vector_store.search(query_embedding, top_k=top_k)
    
    print(f"✓ RAG Retrieval completed")
    print(f"  - Results found: {len(results)}")
    print(f"  - Top-K: {top_k}\n")
    
    # Display results
    for i, result in enumerate(results, 1):
        similarity = result.get('similarity', result.get('score', 0))
        content_preview = result['content'][:200].replace('\n', ' ')
        
        print(f"  [{i}] Relevance: {similarity:.4f}")
        print(f"      Chunk: {result['chunk_id']}")
        print(f"      Page: {result['page_number']}")
        print(f"      Content: {content_preview}...")
        print()
    
    return results


def main():
    """Run complete RAG system demonstration."""
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  RAG SYSTEM FOR LMS - COMPLETE DEMONSTRATION".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Define paths
    pdf_path = Path(__file__).parent / "pdf_sample.pdf"
    output_dir = Path(__file__).parent / "rag_output"
    
    # Check PDF exists
    if not pdf_path.exists():
        print(f"\n✗ ERROR: PDF file not found at {pdf_path}")
        print("\n  Please ensure pdf_sample.pdf exists in the llm/rag directory")
        return 1
    
    try:
        # Phase 1: PDF Processing
        print("\n[STARTING RAG PIPELINE]\n")
        pdf_result = demo_pdf_processing(pdf_path)
        
        # Phase 2: Chunking
        document, chunks_json = demo_chunking(pdf_result, output_dir)
        
        # Phase 3: Embedding & Vector Store
        embedded_doc, vector_store, embedding_service = demo_embedding(document)
        
        # Phase 4: RAG Retrieval
        results = demo_rag_retrieval(
            vector_store,
            embedding_service,
            query="What is the main content?",
            top_k=3,
        )
        
        # Save results summary
        summary = {
            'status': 'success',
            'pipeline': 'PDF -> Chunking -> Embedding -> Vector Store -> Retrieval',
            'pdf_file': str(pdf_path),
            'output_directory': str(output_dir),
            'statistics': {
                'total_pages': document.metadata.get('total_pages', 0),
                'total_chunks': len(document.chunks),
                'total_tokens': sum(c.tokens_count for c in document.chunks),
                'embedding_dimension': embedding_service.embedding_dimension if hasattr(embedding_service, 'embedding_dimension') else 768,
            },
            'retrieval_test': {
                'query': 'What is the main content?',
                'results_count': len(results),
                'top_result_similarity': results[0].get('similarity', results[0].get('score', 0)) if results else 0,
            }
        }
        
        summary_file = output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print_section("PIPELINE COMPLETED SUCCESSFULLY")
        print(f"✓ All phases completed successfully!")
        print(f"\nOutput files:")
        print(f"  - Chunks: {chunks_json}")
        print(f"  - Summary: {summary_file}")
        print(f"\nNext steps:")
        print(f"  1. Integrate with LMS API endpoints")
        print(f"  2. Setup PostgreSQL with pgvector for production")
        print(f"  3. Implement continuous RAG indexing")
        
        return 0
        
    except Exception as e:
        print_section("ERROR")
        print(f"✗ Pipeline failed: {str(e)}")
        logger.exception("RAG pipeline error:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
