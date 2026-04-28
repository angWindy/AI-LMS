# Changelog - AI-LMS Project

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-04-28

### 🎉 RAG System — Vietnamese Semantic Search

#### New Modules
- `llm/rag/pdf_processor.py` — PDF text extraction (PyMuPDF primary, PyPDF2 fallback)
- `llm/rag/chunker.py` — Hierarchical chunker (L0 document → L1 section → L2 paragraph/sentence)
- `llm/rag/embedder.py` — Google Gemini embedding service (`gemini-embedding-001`, 3072 dims)
- `llm/rag/vector_store.py` — InMemoryVectorStore + PostgresVectorStore (pgvector, HNSW index)
- `llm/rag/service.py` — RAGService orchestration layer

#### LMS Backend Integration
- `apps/backend/app/models/rag.py` — 5 SQLAlchemy models: `rag_documents`, `rag_chunks`, `rag_search_sessions`, `rag_search_results`, `rag_integrations`
- `apps/backend/app/schemas/rag.py` — Pydantic request/response schemas
- `apps/backend/app/api/v1/rag.py` — 5 FastAPI endpoints: `/upload`, `/search`, `/documents`, `/documents/{id}`, `/stats`
- `apps/backend/app/services/rag_ingestion.py` — automatic PDF indexing/removal for LMS course and lesson materials
- `apps/backend/scripts/seed_demo_rag.py` — demo course "Tư tưởng Hồ Chí Minh" with two lessons and sample PDFs from `llm/rag/data_sample/`
- Material hierarchy metadata is persisted with every indexed document: `course_id`, `lesson_id`, `material_id`, `uploaded_by`
- Scoped search supports `course_id` and `lesson_id`; cascade cleanup supports material, lesson, and course deletion

#### Bug Fixes
- `sqlalchemy.func` import placed before function definitions in `rag.py` API
- `RAGSearchResult.__repr__` safe for `None` relevance_score
- `get_document_stats` JOIN fixed (`d.id = c.document_id`)
- Vector store search: added `embedding IS NOT NULL` and `is_active = 1` filters
- `PostgresVectorStore` reads connection from `DB_*` env vars and backend `DATABASE_URL`
- Embedding API call updated for `google-genai >= 1.x` (`config={"task_type": ...}`)
- Embedding dimension corrected: `gemini-embedding-001` → 3072 (not 768)
- 3072-dimensional Gemini vectors now skip pgvector HNSW index creation because pgvector approximate indexes are limited to 2000 dimensions
- Chunker skips empty sections from image-based PDFs
- RAG API router is mounted correctly at `/api/v1/rag/*`
- LMS material ingestion reuses the row created by `PostgresVectorStore`, avoiding duplicate `rag_documents` inserts
- RAG chunk IDs are namespaced by document ID before storage so multiple PDFs cannot overwrite each other's chunks
- Docker PostgreSQL image switched to `pgvector/pgvector:pg15` so `CREATE EXTENSION vector` works in local/prod compose

#### Testing
- `llm/rag/test_rag_comprehensive.py` — 7-test suite covering all components + hierarchy invariants
- `llm/rag/test_lms_integration.py` — E2E LMS hierarchy test: ingest six PDFs, course/lesson scoped search, material/lesson/course delete cascade
- All 4 test scripts pass: `test_standalone`, `test_integration`, `test_rag_comprehensive`, `test_lms_integration`
- Real Vietnamese embedding verified: VI↔VI similarity ~0.82–0.93, VI↔EN ~0.66–0.70

#### Dependencies
- Added `pymupdf>=1.23.0` to `apps/backend/requirements.txt`

---

## [0.2.0] - 2026-03-29

### 🎉 Major Additions

#### Backend APIs - Complete Course Management (22 new endpoints)
- **Lessons Management** - 8 endpoints
  - Create, read, update, delete lessons
  - Reorder lessons in course
  - Publish lessons
  - Track lesson progress (watch time, position)

- **Materials Upload** - 3 endpoints
  - Upload materials (videos, documents, images)
  - MIME type validation
  - File size checking
  - List and delete materials

- **Assignments** - 6 endpoints
  - Create assignments with due dates
  - Publish assignments
  - Update and delete assignments
  - List course assignments

- **Submissions** - 5 endpoints
  - Submit assignments (text + file upload)
  - Get personal submissions
  - List all submissions (instructor view)
  - Grade submissions with late penalty
  - Get submission details

### 🔧 Infrastructure Improvements

- **File Upload System**
  - Implemented `app/utils/file_handler.py`
  - MIME type detection with python-magic
  - Secure file storage with unique filenames
  - Directory structure: videos, documents, submissions, materials, thumbnails
  - Static file serving at `/storage/*`

- **Docker Updates**
  - Added libmagic to Dockerfile
  - Proper file storage volume setup

- **Backend Enhancements**
  - Static files mount in main.py
  - New routers registration (lessons, assignments)
  - Updated make start to auto-run migrations
  - Database schema with 12 tables

### ✅ Verification & Testing

- All 22 new endpoints tested and working
- File upload functionality verified
- Grading workflow tested
- Progress tracking confirmed
- Database integrity validated

### 📚 Documentation Updates

- Updated BACKEND_STATUS.md (comprehensive status report)
- Updated PROJECT_OVERVIEW.md (current progress)
- Created this CHANGELOG.md
- Documented all endpoints and their usage

### 🧹 Code Cleanup

- Removed test result logs
- Created storage directory structure with .gitkeep
- Updated .gitignore for cleaner repository
- No unnecessary build artifacts

### 📊 Statistics

- **Total Endpoints**: 49/70 (70% complete)
- **Backend Files**: 6 new files created
- **Lines of Code Added**: ~2000+
- **Database Tables**: 12 (all implemented)
- **API Coverage**: Auth (7/7), Users (8/8), Courses (12/12), Lessons (8/8), Materials (3/3), Assignments (6/6), Submissions (5/5)

---

## [0.1.0] - 2026-03-28

### Initial Release - Core Backend Infrastructure

#### ✅ Completed
- FastAPI application setup
- PostgreSQL database integration
- Alembic migration system
- All 12 database models
- Authentication system (JWT + RBAC)
- User management endpoints (8)
- Course management endpoints (12)
- User endpoints (8)
- Docker containerization
- Comprehensive documentation (6 files)
- Testing infrastructure (test_backend.sh)

#### 📊 Completion
- Infrastructure: 100%
- Authentication: 100%
- Core APIs: ~40% (auth, users, courses)
- Database: 100%
- Documentation: 100%
- Overall: ~35%

---

## Future Roadmap

### High Priority
- [ ] Analytics dashboard (search metrics, course engagement)
- [ ] Notification system (email, in-app)
- [ ] Hybrid search (keyword + vector)
- [ ] Multi-format ingestion (DOCX, TXT)

### Medium Priority
- [ ] OCR for scanned PDFs (pytesseract)
- [ ] Certificate generation
- [ ] Course analytics per student

### Lower Priority
- [ ] Payment integration
- [ ] Video transcoding
- [ ] API rate limiting
- [ ] Real-time WebSocket progress

---

## Technical Details

### Updated Files
- `apps/backend/app/api/v1/lessons.py` (NEW)
- `apps/backend/app/api/v1/assignments.py` (NEW)
- `apps/backend/app/utils/file_handler.py` (NEW)
- `apps/backend/app/api/v1/router.py` (updated)
- `apps/backend/app/main.py` (updated)
- `apps/backend/Dockerfile` (updated)
- `.gitignore` (updated)

### Dependencies
- python-magic (MIME type detection)
- aiofiles (Async file I/O)
- All other dependencies unchanged

### Testing
- Manual endpoint testing: ✅ 22/22 passed
- File upload: ✅ Verified
- Grading workflow: ✅ Verified
- Database consistency: ✅ Verified

---

## Known Issues & TODO

### Improvements Needed
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Refactor to Service/Repository layers
- [ ] Add comprehensive error handling
- [ ] Performance optimization (caching, query optimization)
- [ ] API versioning strategy

### Optional Enhancements
- [ ] Soft deletes for audit trail
- [ ] Webhook system
- [ ] Real-time progress updates (WebSocket)
- [ ] Email templating
- [ ] SMS notifications

---

## Release Notes

### 0.2.0 Summary
This release completes the MVP for basic course management. Students can now:
- Enroll in courses
- View lessons with materials
- Submit assignments
- Get graded work
- Track progress

Instructors can:
- Create courses with lessons
- Upload course materials
- Create assignments
- Grade student work
- View student progress

---

**Maintainers**: [Development Team]  
**Last Updated**: 2026-04-28  
**Repository**: https://github.com/yourusername/AI-LMS
