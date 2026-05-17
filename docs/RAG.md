# RAG System

RAG indexes PDF/DOCX course materials into PostgreSQL with pgvector so chatbot
answers can use lesson/course context.

## Supported Inputs

- PDF: `application/pdf`
- DOCX:
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

External links are not indexed.

## API

```text
POST   /api/v1/rag/upload
POST   /api/v1/rag/search
GET    /api/v1/rag/documents
DELETE /api/v1/rag/documents/{doc_id}
GET    /api/v1/rag/stats
```

Normal LMS uploads should use course/lesson material endpoints. `/rag/upload`
is mainly for ad-hoc testing.

Search:

```json
{
  "query": "Explain the topic",
  "top_k": 5,
  "course_id": "uuid-or-null",
  "lesson_id": "uuid-or-null",
  "document_id": "optional"
}
```

## Flow

1. Material upload stores file and row.
2. `rag_ingestion.py` indexes supported files best-effort.
3. RAG service extracts text, chunks it, embeds it with Gemini, and stores
   `rag_documents` plus `rag_chunks`.
4. Chatbot retrieves lesson-first, then course-level context.

Ingestion failure does not block material upload.

## Config

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
GOOGLE_AI_API_KEY=your-key
```

Embeddings use Gemini `gemini-embedding-001` with 3072 dimensions.

## Main Files

- API/model: `apps/backend/app/api/v1/rag.py`, `apps/backend/app/models/rag.py`
- LMS glue: `apps/backend/app/services/rag_ingestion.py`
- Pipeline: `llm/rag/pdf_processor.py`, `word_processor.py`, `chunker.py`,
  `embedder.py`, `vector_store.py`, `service.py`, `context_builder.py`

## Demo Seed

```bash
PYTHONPATH="$PWD:$PWD/apps/backend" python -m apps.backend.scripts.seed_demo_rag
```
