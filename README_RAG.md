# RAG System Implementation for LMS

## Overview

This document describes the complete RAG (Retrieval Augmented Generation) system implemented for the Learning Management System (LMS). The system enables intelligent document search and retrieval for enhanced learning experiences.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│                  LMS Frontend                        │
├─────────────────────────────────────────────────────┤
│                   API Routes                         │
│              /api/v1/rag/*                           │
├─────────────────────────────────────────────────────┤
│                  RAG Service                         │
│         (High-level RAG operations)                  │
├─────────────────────────────────────────────────────┤
│  PDF Processing │ Chunking │ Embedding │ VectorStore │
├─────────────────────────────────────────────────────┤
│    PostgreSQL Database + pgvector Extension         │
└─────────────────────────────────────────────────────┘
```

### Key Modules

1. **PDF Processor** (`llm/rag/pdf_processor.py`)
   - Extracts text and metadata from PDF documents
   - Preserves page information and document structure
   - Handles multi-page documents efficiently

2. **Hierarchical Chunker** (`llm/rag/chunker.py`)
   - Splits documents into manageable chunks
   - Creates hierarchical structure (document → section → paragraph → sentence)
   - Maintains semantic coherence within chunks
   - Configurable chunk size and overlap

3. **Embedding Service** (`llm/rag/embedder.py`)
   - Generates vector embeddings using Google Gemini models
   - Supports `gemini-embedding-001` and `gemini-embedding-2`
   - Handles both document and query embeddings
   - Calculates cosine similarity for relevance ranking

4. **Vector Store** (`llm/rag/vector_store.py`)
   - In-memory vector store for testing
   - PostgreSQL + pgvector integration for production
   - Cosine similarity search with IVF indexing
   - Document and chunk management

5. **RAG Service** (`llm/rag/service.py`)
   - High-level interface for RAG operations
   - Document ingestion pipeline
   - Search functionality
   - Document deletion and management

6. **Database Models** (`apps/backend/app/models/rag.py`)
   - RAGDocument: Document metadata
   - RAGChunk: Individual content chunks
   - RAGSearchSession: Search history tracking
   - RAGSearchResult: Individual search results
   - RAGIntegration: Document integration with lessons/assignments

7. **API Routes** (`apps/backend/app/api/v1/rag.py`)
   - `POST /api/v1/rag/upload` - Upload PDF documents
   - `POST /api/v1/rag/search` - Search using RAG
   - `GET /api/v1/rag/documents` - List documents
   - `DELETE /api/v1/rag/documents/{doc_id}` - Delete document
   - `GET /api/v1/rag/stats` - System statistics

## Installation & Setup

### 1. Install Dependencies

```bash
cd /home/icthagws/Github/AI-LMS/apps/backend
pip install -r requirements.txt
```

Required packages:
- `PyPDF2>=3.0.1` - PDF processing
- `numpy>=1.24.0` - Vector operations
- `pgvector>=0.2.4` - PostgreSQL vector support
- `google-genai>=1.11.0` - Gemini embeddings (already in requirements)

### 2. Database Setup

```bash
cd apps/backend
alembic upgrade head
```

This creates the following tables:
- `rag_documents` - Document metadata
- `rag_chunks` - Content chunks
- `rag_search_sessions` - Search tracking
- `rag_search_results` - Search results
- `rag_integrations` - LMS integrations

### 3. PostgreSQL with pgvector (Optional, for production)

```bash
# Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# The app will create indexes automatically
CREATE INDEX idx_rag_chunks_embedding 
ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 4. Environment Variables

```bash
# Required for real embeddings
export GOOGLE_AI_API_KEY="your-gemini-api-key"

# Optional database configuration
export DATABASE_URL="postgresql://user:pass@localhost/lms"
```

## Usage

### Uploading Documents

```python
from llm.rag.service import get_rag_service

rag = get_rag_service()
result = rag.ingest_pdf(
    pdf_path="path/to/document.pdf",
    document_id="doc_001"  # Optional
)

print(result)
# Output:
# {
#     'status': 'success',
#     'document_id': 'doc_001',
#     'chunks': 42,
#     'total_tokens': 12500
# }
```

### Searching Documents

```python
result = rag.search(
    query="What is machine learning?",
    top_k=5,  # Return top 5 results
    document_id="doc_001"  # Optional: search in specific document
)

print(result)
# Output:
# {
#     'status': 'success',
#     'query': 'What is machine learning?',
#     'results_count': 5,
#     'results': [
#         {
#             'chunk_id': 'chunk_001_0001',
#             'content': '...',
#             'relevance': 0.87,
#             'page_number': 2
#         },
#         ...
#     ]
# }
```

### API Usage

**Upload Document:**
```bash
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Search:**
```bash
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

**List Documents:**
```bash
curl -X GET http://localhost:8000/api/v1/rag/documents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Chunk Size Configuration

```python
chunker = HierarchicalChunker(
    chunk_size=1000,        # Characters per chunk
    chunk_overlap=100,      # Overlap between chunks
    max_tokens_per_chunk=300,  # Soft token limit
    verbose=True
)
```

### Embedding Models

Available models:
- `gemini-embedding-001` - 768 dimensions
- `gemini-embedding-2` - 768 dimensions
- `text-embedding-004` - 256 dimensions (recommended for speed)

```python
service = EmbeddingService(
    model='gemini-embedding-001',
    api_key='your-api-key'  # Or set GOOGLE_AI_API_KEY env var
)
```

### Vector Store Selection

```python
# In-memory (testing)
from llm.rag.vector_store import InMemoryVectorStore
store = InMemoryVectorStore()

# PostgreSQL (production)
from llm.rag.vector_store import PostgresVectorStore
store = PostgresVectorStore(
    host="localhost",
    port=5432,
    database="lms",
    user="postgres",
    password="postgres"
)
```

## Performance Considerations

### Indexing Strategy

The system uses IVF (Inverted File) indexing for fast similarity search:

```sql
CREATE INDEX idx_rag_chunks_embedding 
ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

Tuning parameters:
- `lists = 100`: More lists = better accuracy but slower indexing
- Adjust based on dataset size and accuracy requirements

### Token Estimation

The system estimates tokens as: `len(content) / 4`

For more accurate estimation, use actual tokenizer:
```python
# Example with Gemini tokenizer
from google.generativeai import protos

def count_tokens(text):
    response = genai.count_message_tokens(
        model="gemini-pro",
        messages=[{"role": "user", "content": text}]
    )
    return response.token_count
```

### Batch Operations

For large-scale ingestion:

```python
documents = [
    "path/to/doc1.pdf",
    "path/to/doc2.pdf",
    # ...
]

rag = get_rag_service()
for doc_path in documents:
    result = rag.ingest_pdf(doc_path)
    print(f"Processed: {result['document_id']}")
```

## Testing

### Standalone Tests

```bash
cd /home/icthagws/Github/AI-LMS
python llm/rag/test_standalone.py
```

### Demo Script

```bash
cd /home/icthagws/Github/AI-LMS
python llm/rag/demo.py
```

### Integration Tests

```bash
cd apps/backend
python -m pytest tests/test_rag.py -v
```

## Analytics & Monitoring

### Search Analytics

The system tracks:
- User search queries
- Result relevance scores
- User feedback (clicking results, ratings)
- Search performance metrics

Access via dashboard or API:

```python
# Get recent searches
searches = db.query(RAGSearchSession).limit(10).all()

# Get user feedback
feedback = db.query(RAGSearchResult)\
    .filter(RAGSearchResult.user_rating != None)\
    .all()

# Average relevance
avg_relevance = db.query(func.avg(RAGSearchResult.relevance_score)).scalar()
```

### Performance Metrics

Monitor:
- Average search latency
- Indexing throughput
- Vector store size
- Hit rate (percentage of successful searches)

## Troubleshooting

### Issue: "Google API key not found"

**Solution:**
```bash
export GOOGLE_AI_API_KEY="your-api-key"
```

Or configure in environment variables file.

### Issue: PostgreSQL connection failed

**Solution:**
```bash
# Check PostgreSQL is running
psql -U postgres -d lms -c "SELECT 1;"

# Verify pgvector installed
psql -U postgres -d lms -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Issue: Slow search performance

**Solution:**
1. Ensure vector indexes are created
2. Adjust IVF list count based on dataset size
3. Consider filtering by document_id to reduce search space
4. Monitor vector store statistics

### Issue: Low relevance scores

**Solution:**
1. Verify embeddings are generated (not using mock zeros)
2. Set GOOGLE_AI_API_KEY for real Gemini embeddings
3. Check chunk size - may be too large/small
4. Review query clarity - ambiguous queries get lower scores

## Integration with LMS

### Lesson Integration

```python
# Attach document to lesson
integration = RAGIntegration(
    lesson_id=lesson.id,
    document_id=doc.id,
    integration_type="supplementary"
)
db.add(integration)
db.commit()
```

### Assignment Integration

```python
# Attach document to assignment
integration = RAGIntegration(
    assignment_id=assignment.id,
    document_id=doc.id,
    integration_type="reference"
)
db.add(integration)
db.commit()
```

### Chatbot Integration

```python
# Use RAG for chatbot context
def get_chatbot_context(question):
    rag = get_rag_service()
    results = rag.search(question, top_k=3)
    
    context = "\n".join([r['content'] for r in results['results']])
    return context
```

## Future Enhancements

1. **Multi-format Support**: Support DOCX, TXT, HTML documents
2. **Advanced Chunking**: Semantic chunking using sentence transformers
3. **Reranking**: Add cross-encoder reranking for better results
4. **Caching**: Implement query result caching
5. **Hybrid Search**: Combine vector and keyword search
6. **Fine-tuning**: Fine-tune embeddings on domain-specific data
7. **Real-time Indexing**: Stream-based document processing
8. **Multi-modal**: Support images, tables, code blocks

## References

- [Gemini Embeddings API](https://ai.google.dev/api/embed-api)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [RAG Best Practices](https://arxiv.org/abs/2312.10997)
- [Vector Database Guide](https://www.pinecone.io/learn/vector-database/)

## License

Same as the main LMS project.

## Support

For issues or questions about the RAG system:

1. Check the logs: `logs/rag_*.log`
2. Run tests: `python llm/rag/test_standalone.py`
3. Review documentation: This README and code comments
4. Check GitHub issues: [AI-LMS Issues](https://github.com/your-repo/issues)
