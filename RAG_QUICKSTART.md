# RAG System Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies (1 minute)

```bash
cd /home/icthagws/Github/AI-LMS/apps/backend
pip install -r requirements.txt
```

### 2. Run Database Migration (1 minute)

```bash
alembic upgrade head
```

This creates the RAG tables in your PostgreSQL database.

### 3. Set API Key (Optional, for real embeddings)

```bash
export GOOGLE_AI_API_KEY="your-gemini-api-key"
```

Without this, the system uses mock embeddings (for testing only).

### 4. Verify Installation (1 minute)

```bash
cd /home/icthagws/Github/AI-LMS
python llm/rag/test_standalone.py
```

Expected output: All tests passing ✓

### 5. Start Server (1 minute)

```bash
cd apps/backend
python main.py
```

Server will start at `http://localhost:8000`

## Common Operations

### Upload a PDF Document

```python
from llm.rag.service import get_rag_service

rag = get_rag_service()

# Ingest a PDF
result = rag.ingest_pdf("documents/textbook.pdf", document_id="textbook_001")

if result['status'] == 'success':
    print(f"✓ Uploaded {result['chunks']} chunks")
    print(f"  Document ID: {result['document_id']}")
else:
    print(f"✗ Error: {result['error']}")
```

### Search Documents

```python
# Search for relevant content
results = rag.search(
    query="What is machine learning?",
    top_k=5  # Get top 5 results
)

if results['status'] == 'success':
    for i, result in enumerate(results['results'], 1):
        relevance = result['relevance']
        print(f"{i}. [Relevance: {relevance:.2%}]")
        print(f"   {result['content'][:200]}...\n")
```

### Via REST API

```bash
# Upload PDF
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "machine learning", "top_k": 5}'

# List documents
curl -X GET http://localhost:8000/api/v1/rag/documents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

### Environment Variables

```bash
# Required for real embeddings
GOOGLE_AI_API_KEY=your-api-key

# Optional database settings
DATABASE_URL=postgresql://user:pass@localhost/lms
LOG_LEVEL=INFO
```

### Chunking Parameters

```python
from llm.rag.chunker import HierarchicalChunker

chunker = HierarchicalChunker(
    chunk_size=1000,           # Characters per chunk
    chunk_overlap=100,         # Overlap between chunks
    max_tokens_per_chunk=300,  # Token limit
)
```

### Embedding Models

Available models (choose based on your needs):

| Model | Dimensions | Speed | Cost |
|-------|-----------|-------|------|
| gemini-embedding-001 | 768 | Medium | Low |
| gemini-embedding-2 | 768 | Fast | Low |
| text-embedding-004 | 256 | Very Fast | Very Low |

```python
from llm.rag.embedder import EmbeddingService

# Use fast model with smaller dimensions
service = EmbeddingService(model='text-embedding-004')
```

## Troubleshooting

### Issue: API key not found error

```bash
# Check if env var is set
echo $GOOGLE_AI_API_KEY

# Set it
export GOOGLE_AI_API_KEY="your-api-key"

# Or use .env file
echo "GOOGLE_AI_API_KEY=your-api-key" >> .env
```

### Issue: Database table not found

```bash
# Run migrations
cd apps/backend
alembic upgrade head

# Verify tables exist
psql -U postgres -d lms -c "\dt rag_*"
```

### Issue: Slow search performance

1. Check if vector index is created:
   ```sql
   SELECT indexname FROM pg_indexes 
   WHERE tablename = 'rag_chunks';
   ```

2. Ensure pgvector is installed:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. Consider filtering by document:
   ```python
   results = rag.search(query, document_id="specific_doc_001")
   ```

### Issue: Low relevance scores (always 0.0)

This usually means mock embeddings are being used (all zeros).

**Solution**: Set GOOGLE_AI_API_KEY for real Gemini embeddings

```bash
export GOOGLE_AI_API_KEY="your-api-key"
# Restart the server
```

## Example: Complete Workflow

```python
"""
Complete RAG workflow example
"""
from llm.rag.service import get_rag_service

# Initialize
rag = get_rag_service(use_postgres=False)  # Use in-memory for testing

# 1. Ingest document
print("1. Ingesting PDF...")
result = rag.ingest_pdf("lecture_notes.pdf", document_id="lecture_001")
print(f"   ✓ Created {result['chunks']} chunks")

# 2. Search for information
print("\n2. Searching for 'neural networks'...")
results = rag.search("What are neural networks?", top_k=3)

# 3. Display results
print(f"\n3. Found {results['results_count']} relevant sections:\n")
for i, chunk in enumerate(results['results'], 1):
    print(f"Result {i}: Relevance {chunk['relevance']:.1%}")
    print(f"  Page {chunk['page_number']}: {chunk['content'][:150]}...\n")

# 4. Delete when done
print("4. Cleanup...")
rag.delete_document("lecture_001")
print("   ✓ Document deleted")
```

## Next Steps

1. **Integrate with lessons**:
   ```python
   # Attach RAG document to lesson
   from app.models.rag import RAGIntegration
   
   integration = RAGIntegration(
       lesson_id=lesson.id,
       document_id=doc.id,
       integration_type="supplementary"
   )
   ```

2. **Add to chatbot**:
   ```python
   # Get context for chatbot responses
   context = rag.search(user_question, top_k=5)
   # Pass context to LLM for better responses
   ```

3. **Monitor analytics**:
   ```python
   # Track search patterns
   from app.models.rag import RAGSearchSession
   
   searches = db.query(RAGSearchSession)\
       .filter(RAGSearchSession.user_id == user_id)\
       .all()
   ```

## Performance Tips

1. **Batch uploads**: Upload multiple documents in parallel
2. **Query caching**: Cache popular searches
3. **Hybrid search**: Combine vector search with keyword matching
4. **Fine-tuning**: Fine-tune embeddings on domain data
5. **Reranking**: Use cross-encoders for better ranking

## File Locations

- **Core RAG**: `/home/icthagws/Github/AI-LMS/llm/rag/`
- **LMS Integration**: `/home/icthagws/Github/AI-LMS/apps/backend/app/`
- **Tests**: `/home/icthagws/Github/AI-LMS/llm/rag/test_*.py`
- **Documentation**: `/home/icthagws/Github/AI-LMS/README_RAG.md`
- **Demo**: `/home/icthagws/Github/AI-LMS/llm/rag/demo.py`

## Support

- **Tests**: `python llm/rag/test_standalone.py`
- **Demo**: `python llm/rag/demo.py`
- **Logs**: Check `logs/` directory
- **Docs**: See `README_RAG.md` for detailed documentation

## Production Checklist

- [ ] PostgreSQL with pgvector extension installed
- [ ] GOOGLE_AI_API_KEY set in environment
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Vector indexes created
- [ ] Error logging configured
- [ ] Rate limiting enabled
- [ ] Monitoring alerts set up
- [ ] Backup strategy configured
- [ ] Load testing completed
- [ ] Security audit passed

---

For more information, see **README_RAG.md** or check the code comments in `/llm/rag/` and `/app/models/rag.py`.
