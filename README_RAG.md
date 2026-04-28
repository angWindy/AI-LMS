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
DATABASE_URL=postgresql://lms_user:lms_password@localhost:5432/lms_db
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
```

`gemini-embedding-001` uses 3072-dimensional vectors. pgvector approximate indexes currently support up to 2000 dimensions for `vector`, so the 3072d store uses exact cosine scan by default. Add a projection or `halfvec` strategy later if the corpus grows enough to need approximate indexing.

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

## LMS Material Integration

Teacher uploads through the normal LMS material endpoints are indexed automatically when the backend can process the file type. PDF documents are currently supported.

| LMS action | RAG behavior |
|------------|--------------|
| `POST /api/v1/courses/{course_id}/materials` with PDF | Ingests course-level material with `course_id` + `material_id` |
| `POST /api/v1/lessons/{lesson_id}/materials` with PDF | Ingests lesson material with `course_id` + `lesson_id` + `material_id` |
| Delete material | Deletes matching RAG document/chunks by `material_id` |
| Delete lesson | Deletes all RAG documents/chunks for that `lesson_id` |
| Delete course | Deletes all RAG documents/chunks for that `course_id` |

The glue code lives in `apps/backend/app/services/rag_ingestion.py`. It is fail-soft: upload/delete requests still complete if indexing cleanup fails, and errors are logged.

Search can be scoped:

```json
{
  "query": "cách mạng giải phóng dân tộc",
  "top_k": 5,
  "course_id": "<course-uuid>",
  "lesson_id": "<lesson-uuid>"
}
```

### Classroom Chatbot RAG

`POST /api/v1/chatbot/ask` now performs backend RAG retrieval automatically when `course_id` and/or `lesson_id` are provided. The frontend only needs to send the classroom scope; it does not need to pre-build `context_docs`.

Context priority:

| Condition | Retrieval behavior |
|-----------|--------------------|
| Lesson has indexed PDF material | `CONTEXT_CHINH_LESSON`: search only documents where `lesson_id` matches the classroom lesson |
| Course has course-level indexed PDF material | `CONTEXT_PHU_COURSE`: search only course-level documents where `course_id` matches and `lesson_id IS NULL` |
| Lesson has no indexed PDF material | course-level results are marked `CONTEXT_CHINH_COURSE` |

The system prompt always includes:

- course title
- lesson/classroom title
- assistant role as a teaching assistant for that course
- instruction to answer in Vietnamese, concise and accurate
- instruction to prefer lesson context before course context

Example classroom request:

```bash
curl -X POST http://localhost:8000/api/v1/chatbot/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "question": "Tóm tắt ngắn gọn ý chính của tài liệu trong buổi học này",
    "course_id": "<course-uuid>",
    "lesson_id": "<lesson-uuid>"
  }'
```

The response includes `context.rag_context` so you can verify whether the retrieved blocks are labelled `CONTEXT_CHINH_LESSON`, `CONTEXT_PHU_COURSE`, or `CONTEXT_CHINH_COURSE`.

### Delete Cleanup Verification

When a material is deleted from the LMS database via:

- `DELETE /api/v1/lessons/materials/{material_id}`
- `DELETE /api/v1/courses/materials/{material_id}`

the backend calls `remove_material_index(...)`, which deletes the linked `rag_documents` row by `material_id`. `rag_chunks` are removed by the database foreign key cascade.

Quick SQL check:

```sql
SELECT doc_id, material_id FROM rag_documents WHERE material_id = '<material-uuid>';
SELECT c.chunk_id
FROM rag_chunks c
JOIN rag_documents d ON d.id = c.document_id
WHERE d.material_id = '<material-uuid>';
```

Both queries should return zero rows after deletion.

### Demo Seed

Create the demo course **"Tư tưởng Hồ Chí Minh"**, two lessons, and six PDF materials from `llm/rag/data_sample/`:

```bash
python -m apps.backend.scripts.seed_demo_rag
```

The seed script refreshes existing demo materials and indexes them into RAG.

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
Stored `chunk_id` values are namespaced by `document_id` to keep chunks from different PDFs isolated in PostgreSQL.

> ⚠️ **Image-based / scanned PDFs** produce 0 extractable text.  
> OCR (e.g. `pytesseract`) would be required to index them.

---

## Running Tests

```bash
# Classroom chatbot RAG: lesson-primary context, course supplementary context,
# and course_only vector search behavior
python -m llm.rag.test_chatbot_classroom_rag

# LMS hierarchy E2E: ingest, course/lesson scoped search, material/lesson/course delete cascade
python -m llm.rag.test_lms_integration

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
| `extension "vector" is not available` | Use the `pgvector/pgvector:pg15` Docker image or install pgvector in PostgreSQL |
| All search relevance scores are 0 | API key missing → mock zero vectors returned |
| PDF gives 0 chars | Scanned/image-based PDF; requires OCR |
| Low relevance on Vietnamese text | Use `gemini-embedding-001` (not `text-embedding-004`) |
