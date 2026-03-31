# AI-LMS Project Overview

## 📌 About

AI-LMS is a Learning Management System built with:
- **Backend**: FastAPI + PostgreSQL (Docker)
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Features**: Course management, lessons, materials, assignments, file uploads

## 🎯 Project Status

### ✅ Completed (95%)

**Backend Infrastructure**
- FastAPI API with 49+ endpoints
- PostgreSQL database (12 tables, Alembic migrations)
- Docker production deployment with Nginx
- File upload system (videos, documents, images)
- Static file serving via Nginx

**Frontend (Next.js)**
- Authentication: Login, Register, JWT token management
- Dashboard: Role-based (Admin, Instructor, Student)
- Course management: Browse, Enroll/Unenroll, Create/Edit
- Lesson management: Create, Edit, Video playback (YouTube/Vimeo)
- Materials: Upload/Download for teachers, View for students
- Progress tracking: Video position saved automatically
- Responsive UI with shadcn/ui components

**Core Features**
- Authentication: Register, login, JWT tokens, refresh
- Authorization: 3 roles (Admin, Instructor, Learner)
- User Management: CRUD operations
- Course Management: Full CRUD with enrollment/unenrollment
- Lessons: CRUD + materials (upload/download) + video embed
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

### 🔄 In Progress

**AI Features**: 0% (Phase 3)
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
│   │   ├── storage/      # Uploaded files storage
│   │   └── Dockerfile
│   └── frontend/         # Next.js 14 frontend
│       ├── src/
│       │   ├── app/      # App Router pages
│       │   ├── components/ # UI components (shadcn/ui)
│       │   └── lib/      # API clients, auth, utilities
│       └── Dockerfile
├── docker/
│   └── nginx/            # Nginx reverse proxy config
├── docs/                 # Documentation
├── docker-compose.yml    # Local development
├── docker-compose.prod.yml # Production deployment
└── Makefile             # Development commands
```

## 🚀 Quick Start

### Development
```bash
git clone <repo>
cd AI-LMS
cp .env.example .env
make start       # Backend + DB only
```

### Production (Docker)
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Access
- Frontend: http://localhost (via Nginx)
- API: http://localhost/api/v1
- Swagger: http://localhost/api/docs

### Default Accounts
- Admin: admin@test.com / 00000000
- Teacher: teacher@test.com / 00000000
- Student: student@test.com / 00000000

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

### Frontend Testing (Manual)
1. Login with test accounts (admin/teacher/student)
2. Browse courses
3. Enroll/Unenroll from courses
4. Access lesson details
5. Watch video (YouTube embed)
6. Download materials
7. (Teacher) Upload materials
8. (Teacher) Create/edit lessons

### Backend Testing
Via Swagger UI at `/api/docs`:
- Create users (admin, instructor, student)
- Enroll in courses
- Upload lessons and materials
- Submit assignments
- Grade submissions
- Track progress

## 📋 Next Steps (Phase 3)

1. Admin panel (full user management)
2. AI chatbot integration
3. Assignment submission UI
4. Progress analytics dashboard
5. Performance optimization
6. Unit tests

## 📞 Key Technologies

**Backend**
- Python 3.11 + FastAPI 0.109
- PostgreSQL 15 with SQLAlchemy ORM
- Alembic for migrations
- JWT for authentication
- python-magic for MIME detection

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- Zustand for state management
- Axios for API calls

**Infrastructure**
- Docker + Docker Compose
- Nginx reverse proxy
- PostgreSQL 15

---

**Status**: Phase 2 Complete (95%)  
**Last Updated**: 2026-03-31
