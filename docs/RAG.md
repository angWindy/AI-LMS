# RAG System

The RAG pipeline lets AI-LMS answer course questions from uploaded PDF materials.

## Flow

1. Extract text from PDF files.
2. Split text into chunks.
3. Generate embeddings with Gemini.
4. Store vectors in PostgreSQL with pgvector.
5. Retrieve relevant chunks for chatbot requests.
6. Build an LLM prompt from course, lesson, and retrieved context.

## Main Files

- `llm/rag/pdf_processor.py`: PDF text extraction.
- `llm/rag/chunker.py`: text chunking.
- `llm/rag/embedder.py`: Gemini embedding client.
- `llm/rag/vector_store.py`: pgvector storage and search.
- `llm/rag/context_builder.py`: prompt context builder.
- `llm/rag/service.py`: orchestration service.
- `apps/backend/app/services/rag_ingestion.py`: backend ingestion integration.
- `apps/backend/app/api/v1/rag.py`: RAG API routes.

## Configuration

```env
GOOGLE_AI_API_KEY=your-key
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
```

`gemini-embedding-001` returns 3072-dimensional vectors. The project uses exact cosine search by default because common pgvector approximate indexes have dimension limits.

## Verification

```bash
python -m pytest -q tests
```

Use `apps/backend/scripts/seed_demo_rag.py` when you need demo data from `llm/rag/data_sample/`.
