# RAG System — AI-LMS

Retrieval-Augmented Generation (RAG) pipeline for the LMS. Ingests PDF documents, generates vector embeddings via Google Gemini, and retrieves semantically relevant chunks at query time.

Supports **Vietnamese** and multilingual content natively (`gemini-embedding-001`, 3072 dims).

---

## Architecture

```
PDF file
  └─▶ PDFProcessor          (PyMuPDF → PyPDF2 fallback)
        └─▶ HierarchicalChunker
              L0: Document root
              L1: Page sections
              L2: Paragraphs / Sentences
              └─▶ EmbeddingService   (Gemini gemini-embedding-001, 3072d)
                    └─▶ VectorStore  (InMemory | PostgreSQL+pgvector)
                          └─▶ RAGService   ◀── /api/v1/rag/*
```

### Modules

| Module | Path | Role |
|--------|------|------|
| PDFProcessor | `llm/rag/pdf_processor.py` | Text + metadata extraction |
| HierarchicalChunker | `llm/rag/chunker.py` | Hierarchy-aware chunking |
| EmbeddingService | `llm/rag/embedder.py` | Gemini vector embeddings |
| VectorStore | `llm/rag/vector_store.py` | In-memory & PostgreSQL stores |
| RAGService | `llm/rag/service.py` | Orchestration layer |
| DB Models | `apps/backend/app/models/rag.py` | SQLAlchemy ORM |
| API Routes | `apps/backend/app/api/v1/rag.py` | FastAPI endpoints |

---

## Setup

### 1. Install dependencies

```bash
pip install -r apps/backend/requirements.txt
```

Key RAG packages: `pymupdf`, `PyPDF2`, `numpy`, `pgvector`, `google-genai`

### 2. Environment

```bash
# .env
GOOGLE_AI_API_KEY=your-gemini-api-key   # required for real embeddings

# DB (defaults work for local Docker setup)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lms_db
DB_USER=lms_user
DB_PASSWORD=lms_password
```

### 3. Database migrations

```bash
cd apps/backend
alembic upgrade head
```

Creates: `rag_documents`, `rag_chunks`, `rag_search_sessions`, `rag_search_results`, `rag_integrations`

### 4. pgvector (production)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- HNSW index created automatically on first run
```

---

## Embedding Models

| Model | Dimensions | Notes |
|-------|-----------|-------|
| `gemini-embedding-001` | 3072 | Default, best quality, multilingual |
| `text-embedding-004` | 768 | Smaller, faster |

Without `GOOGLE_AI_API_KEY` the service initialises but returns zero vectors (mock mode). Set the key for semantic search.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/rag/upload` | Upload & ingest a PDF |
| POST | `/api/v1/rag/search` | Semantic search |
| GET | `/api/v1/rag/documents` | List ingested documents |
| DELETE | `/api/v1/rag/documents/{doc_id}` | Delete document |
| GET | `/api/v1/rag/stats` | System stats |

All endpoints require `Authorization: Bearer <token>`.

**Upload:**
```bash
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@lecture.pdf" -F "title=Lecture 1" \
  -H "Authorization: Bearer $TOKEN"
```

**Search:**
```bash
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "tư tưởng Hồ Chí Minh về dân tộc", "top_k": 5}'
```

---

## Python Usage

```python
from llm.rag.service import get_rag_service

rag = get_rag_service()

# Ingest
result = rag.ingest_pdf("lecture.pdf", document_id="lesson_01")
# {'status': 'success', 'chunks': 33, 'pages': 9, ...}

# Search
hits = rag.search("nguồn gốc tư tưởng Hồ Chí Minh", top_k=3)
for r in hits["results"]:
    print(r["relevance"], r["content"][:80])

# Delete
rag.delete_document("lesson_01")
```

---

## Data Hierarchy

Chunks follow a strict 3-level tree — each invariant is verified by the test suite:

```
L0  document   (1 per PDF, root node)
 └─ L1  section    (1 per non-empty page)
     └─ L2  paragraph / sentence  (content nodes, embedded)
```

Structural nodes (L0, L1) are **never** included in search results.

> ⚠️ **Image-based / scanned PDFs** produce 0 extractable text.  
> OCR (e.g. `pytesseract`) would be required to index them.

---

## Running Tests

```bash
# Comprehensive test suite (all components + hierarchy + data samples)
python -m llm.rag.test_rag_comprehensive

# Standalone component tests
python -m llm.rag.test_standalone

# Integration tests (models, schemas, API router)
python -m llm.rag.test_integration
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Google API key not found` | Set `GOOGLE_AI_API_KEY` in `.env` |
| PostgreSQL connection failed | Check `DB_*` env vars; run `psql` to verify |
| All search relevance scores are 0 | API key missing → mock zero vectors returned |
| PDF gives 0 chars | Scanned/image-based PDF; requires OCR |
| Low relevance on Vietnamese text | Use `gemini-embedding-001` (not `text-embedding-004`) |
