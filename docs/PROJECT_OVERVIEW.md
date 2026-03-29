# AI-LMS Project Overview

## 📌 About

AI-LMS is a Learning Management System built with:
- **Backend**: FastAPI + PostgreSQL (Docker)
- **Frontend**: Next.js (Phase 2)
- **Features**: Course management, lessons, assignments, file uploads

## 🎯 Phase 1 - MVP Status

### ✅ Completed (70%)

**Backend Infrastructure**
- FastAPI API with 49 endpoints
- PostgreSQL database (12 tables, Alembic migrations)
- Docker deployment with auto-migrations
- File upload system (videos, documents, images)

**Core Features**
- Authentication: Register, login, JWT tokens, refresh
- Authorization: 3 roles (Admin, Instructor, Learner)
- User Management: CRUD operations
- Course Management: Full CRUD with enrollment
- Lessons: CRUD + materials (upload/download)
- Assignments: CRUD + submissions + grading
- Progress Tracking: Per-lesson and course-wide

**API Endpoints**: 49/70 (70%)
- Authentication (7/7) ✅
- Users (8/8) ✅
- Courses (12/12) ✅
- Lessons (8/8) ✅
- Materials (3/3) ✅
- Assignments (6/6) ✅
- Submissions (5/5) ✅

### ❌ Not Started

**Frontend**: 0% (Phase 2)
- React/Next.js dashboard
- Admin panel
- Student interface
- Instructor tools

**AI Features**: 0% (Phase 2)
- Chatbot assistant
- Personalized recommendations
- Progress analytics

## 📂 Project Structure

```
AI-LMS/
├── apps/
│   ├── backend/          # FastAPI application
│   │   ├── app/
│   │   │   ├── api/v1/   # API endpoints (routes)
│   │   │   ├── models/   # SQLAlchemy models (database)
│   │   │   ├── schemas/  # Pydantic schemas (validation)
│   │   │   ├── utils/    # Utilities (file handling, auth)
│   │   │   └── main.py   # FastAPI app entry
│   │   └── Dockerfile
│   └── frontend/         # Next.js frontend (scaffold)
├── services/             # Microservices (future)
├── docs/                 # Documentation
├── docker-compose.yml    # Local development setup
└── Makefile             # Development commands
```

## 🚀 Quick Start

```bash
# Setup
git clone <repo>
cd AI-LMS
cp .env.example .env

# Start (with auto-migrations)
make start

# Access
Backend API:  http://localhost:8000
Swagger UI:   http://localhost:8000/docs
ReDoc:        http://localhost:8000/redoc
```

## 🗄️ Database

**12 Tables**:
- users (Admin, Instructor, Learner)
- courses (with enrollment)
- lessons (with progress tracking)
- materials (course materials/videos)
- assignments (with submissions)
- submissions (with grades)
- notifications, activity_logs, etc.

All with proper relationships and cascade deletes.

## 🔐 Authentication

- **Register/Login**: Email + password (bcrypt hashed)
- **Tokens**: JWT (15min access, 7day refresh)
- **Roles**: Admin (full access), Instructor (manage courses), Learner (view courses)
- **Permissions**: Enforced on every endpoint

## 📤 File Upload

Supports:
- **Videos**: up to 500MB
- **Documents**: up to 50MB (PDF, DOCX, PPTX, TXT)
- **Images**: up to 10MB

Files stored in `/storage/{type}/` with MIME validation and secure names.

## 🧪 Testing

Manual tests via Swagger UI:
- Create users (admin, instructor, student)
- Enroll in courses
- Upload lessons and materials
- Submit assignments
- Grade submissions
- Track progress

See `test_backend.sh` in root for examples.

## 📋 Next Steps (Phase 2)

1. Frontend dashboard (React/Next.js)
2. Admin panel (user management)
3. Student & instructor interfaces
4. AI chatbot integration
5. Analytics dashboard
6. Performance optimization
7. Unit tests

## 📞 Key Technologies

- **Python 3.11** + FastAPI 0.109
- **PostgreSQL 15** with SQLAlchemy ORM
- **Docker** for containerization
- **JWT** for authentication
- **Alembic** for migrations
- **python-magic** for MIME detection

---

**Status**: MVP Phase 1 - 70% Complete  
**Last Updated**: 2026-03-29
