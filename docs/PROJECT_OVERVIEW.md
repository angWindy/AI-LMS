# AI-LMS Project Overview

## Tổng quan dự án

AI-LMS (AI-powered Learning Management System) là một hệ thống quản lý học tập hiện đại được xây dựng với kiến trúc microservices, sử dụng FastAPI cho backend và Next.js cho frontend (đang phát triển).

## 🎯 Mục tiêu dự án

### Mục tiêu chính
- Xây dựng một nền tảng LMS hoàn chỉnh với khả năng mở rộng cao
- Tích hợp AI để hỗ trợ giảng dạy và học tập
- Cung cấp trải nghiệm người dùng hiện đại và dễ sử dụng
- Hỗ trợ video streaming và theo dõi tiến độ học tập

### Các tính năng chính
1. **Quản lý người dùng** với 3 vai trò: Admin, Instructor, Learner
2. **Quản lý khóa học** đầy đủ (CRUD operations)
3. **Quản lý bài giảng** với hỗ trợ video
4. **Hệ thống bài tập và nộp bài**
5. **Theo dõi tiến độ học tập** chi tiết
6. **Tích hợp AI Assistant** (đang phát triển)
7. **Dashboard phân tích** (đang phát triển)

## 📊 Tiến độ dự án hiện tại

### Phase 1 - MVP (Hiện tại - 70% hoàn thành) ✅

#### ✅ Đã hoàn thành
- **Backend Infrastructure** (100%)
  - FastAPI application setup
  - Docker containerization with auto-migration
  - PostgreSQL database integration (Alembic)
  - All 12 database models with relationships
  - Static file serving for uploads

- **Authentication & Authorization** (100%)
  - JWT authentication (access + refresh tokens)
  - Role-based access control (Admin, Instructor, Learner)
  - Password hashing (bcrypt)
  - Token refresh mechanism
  - Current user dependency injection

- **API Endpoints** (49/70 ~ 70%)
  
  **Authentication** (7/7) ✅
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
  - POST /auth/logout
  - GET /auth/me
  - PUT /auth/me
  - PUT /auth/me/password

  **Users** (8/8) ✅
  - GET /users, POST /users
  - GET /users/{id}, PUT /users/{id}, DELETE /users/{id}
  - POST /users/{id}/activate, deactivate, verify

  **Courses** (12/12) ✅
  - GET /courses, POST /courses
  - GET /courses/{id}, PUT /courses/{id}, DELETE /courses/{id}
  - GET /courses/slug/{slug}
  - POST /courses/{id}/publish, archive
  - GET /courses/{id}/lessons
  - POST /courses/{id}/enroll
  - GET /courses/my/teaching, my/enrolled

  **Lessons** (8/8) ✅ **NEW**
  - POST /lessons?course_id={id}
  - GET /lessons/{id}
  - PUT /lessons/{id}
  - DELETE /lessons/{id}
  - PATCH /lessons/{id}/order
  - POST /lessons/{id}/publish
  - POST /lessons/{id}/progress
  - GET /lessons/{id}/progress

  **Materials** (3/3) ✅ **NEW**
  - POST /lessons/{id}/materials (with file upload)
  - GET /lessons/{id}/materials
  - DELETE /lessons/materials/{id}

  **Assignments** (6/6) ✅ **NEW**
  - POST /assignments?course_id={id}
  - GET /assignments?course_id={id}
  - GET /assignments/{id}
  - PUT /assignments/{id}
  - DELETE /assignments/{id}
  - POST /assignments/{id}/publish

  **Submissions** (5/5) ✅ **NEW**
  - POST /assignments/{id}/submit (with file)
  - GET /assignments/{id}/my-submission
  - GET /assignments/{id}/submissions
  - POST /submissions/{id}/grade
  - GET /submissions/{id}

- **File Upload System** (100%) ✅ **NEW**
  - MIME type validation (python-magic)
  - File size checking
  - Secure storage
  - Video (500MB), document (50MB), image (10MB) support
  - Unique filename generation
  - Static file serving at /storage/*

#### 🟡 Chưa hoàn thành (Phase 2)
- **AI Features** (0%)
  - AI conversation endpoints
  - AI message handling
  - LLM integration
  
- **Advanced Features** (0%)
  - Notifications system
  - Analytics & reporting
  - Search & filtering
  - Certificates
  
- **Frontend** (0%)
  - Scaffolding exists
  - No components implemented
  
- **Testing** (0%)
  - Unit tests
  - Integration tests
  - E2E tests
  - Chưa có service implementation
  - Chưa tích hợp LLM providers

### Phase 2 - Advanced Features (Kế hoạch)
- Frontend hoàn chỉnh với Next.js + shadcn/ui
- Video streaming optimization
- AI Assistant integration
- Analytics dashboard
- Real-time notifications
- Mobile responsive design

## 🏗️ Kiến trúc hệ thống

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Web Browser │  │  Mobile App  │  │  Desktop App │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─── HTTP/HTTPS (REST API)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Next.js Frontend (Port 3000)              │  │
│  │  - Server-side rendering                             │  │
│  │  - Client-side routing                               │  │
│  │  - State management                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─── REST API Calls
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          FastAPI Backend (Port 8000)                 │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │ Auth API   │  │  Course API  │  │  User API  │  │  │
│  │  └────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                      │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │        JWT Middleware & CORS                  │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼──────────────┐
              ↓             ↓              ↓
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Service    │ │   Service    │ │   Service    │
    │   Layer     │ │    Layer     │ │    Layer     │
    │  (Planned)  │ │  (Planned)   │ │  (Planned)   │
    └─────────────┘ └──────────────┘ └──────────────┘
                            │
              ┌─────────────┼──────────────┐
              ↓             ↓              ↓
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Repository  │ │  Repository  │ │  Repository  │
    │    Layer    │ │    Layer     │ │    Layer     │
    │  (Planned)  │ │  (Planned)   │ │  (Planned)   │
    └─────────────┘ └──────────────┘ └──────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        PostgreSQL Database (Port 5432)               │  │
│  │  ┌────────┐ ┌─────────┐ ┌───────────┐ ┌──────────┐ │  │
│  │  │ Users  │ │ Courses │ │  Lessons  │ │Materials │ │  │
│  │  └────────┘ └─────────┘ └───────────┘ └──────────┘ │  │
│  │  ┌──────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │Enrollment│ │ Assignments │ │  Submissions    │  │  │
│  │  └──────────┘ └─────────────┘ └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ File Storage │  │ Video CDN    │  │  Cache Layer │     │
│  │  (Planned)   │  │  (Planned)   │  │  (Planned)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AI Services (Future)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Chatbot    │  │   Analytics  │  │Recommendation│     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Backend Architecture (Clean Architecture Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
│  /api/v1/auth, /api/v1/users, /api/v1/courses              │
│  - Route handlers                                           │
│  - Request/Response validation (Pydantic)                   │
│  - Dependency injection                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Planned)                   │
│  - Business logic                                           │
│  - Domain rules                                             │
│  - Transaction management                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Repository Layer (Planned)                  │
│  - Data access abstraction                                  │
│  - Query builders                                           │
│  - ORM interactions                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Model Layer (SQLAlchemy)                 │
│  - ORM models                                               │
│  - Database relationships                                   │
│  - Constraints and validations                              │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Cấu trúc thư mục chi tiết

```
AI-LMS/
├── apps/                           # Application code
│   ├── backend/                    # FastAPI backend (ACTIVE)
│   │   ├── app/                    # Main application code
│   │   │   ├── api/v1/            # API endpoints (880 lines)
│   │   │   │   ├── auth.py        # Authentication (203 lines)
│   │   │   │   ├── users.py       # User management (230 lines)
│   │   │   │   ├── courses.py     # Course management (434 lines)
│   │   │   │   └── router.py      # Main router
│   │   │   ├── core/              # Core configuration
│   │   │   │   ├── config.py      # Settings management
│   │   │   │   ├── security.py    # JWT & password hashing
│   │   │   │   ├── dependencies.py # FastAPI dependencies
│   │   │   │   └── exceptions.py  # Custom exceptions
│   │   │   ├── db/                # Database layer
│   │   │   │   ├── base.py        # SQLAlchemy base
│   │   │   │   ├── session.py     # DB session factory
│   │   │   │   └── migrations/    # Alembic migrations
│   │   │   ├── models/            # SQLAlchemy ORM (756 lines)
│   │   │   │   ├── user.py
│   │   │   │   ├── course.py
│   │   │   │   ├── lesson.py
│   │   │   │   ├── material.py
│   │   │   │   ├── assignment.py
│   │   │   │   ├── enrollment.py
│   │   │   │   ├── lesson_progress.py
│   │   │   │   ├── submission.py
│   │   │   │   ├── refresh_token.py
│   │   │   │   └── ai_interaction.py
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   │   ├── user.py
│   │   │   │   ├── course.py
│   │   │   │   ├── lesson.py
│   │   │   │   ├── assignment.py
│   │   │   │   └── common.py
│   │   │   ├── services/          # Business logic (EMPTY)
│   │   │   ├── repositories/      # Data access (EMPTY)
│   │   │   ├── utils/             # Utilities
│   │   │   │   ├── file_handler.py
│   │   │   │   └── permissions.py
│   │   │   └── main.py            # FastAPI app entry
│   │   ├── tests/                 # Tests (EMPTY)
│   │   ├── Dockerfile             # Docker build config
│   │   ├── alembic.ini           # Migration config
│   │   └── requirements.txt       # Python dependencies
│   │
│   └── frontend/                  # Next.js frontend (PLANNED)
│       ├── app/                   # Next.js 14 app directory
│       ├── components/            # React components (EMPTY)
│       ├── features/              # Feature modules (EMPTY)
│       ├── hooks/                 # Custom hooks (EMPTY)
│       └── styles/                # CSS/Tailwind (EMPTY)
│
├── services/                      # Microservices (Future)
│   └── ai/                        # AI services (PLANNED)
│       ├── chatbot/               # AI chatbot (EMPTY)
│       ├── analytics/             # Analytics service (EMPTY)
│       └── recommendation/        # Recommendation (EMPTY)
│
├── packages/                      # Shared packages (Future)
│
├── tests/                         # Integration tests (EMPTY)
│   ├── api/
│   └── web/
│
├── docs/                          # Documentation
│   ├── PROJECT_OVERVIEW.md        # This file
│   ├── DATABASE_SCHEMA.md         # Database documentation
│   ├── API_DOCUMENTATION.md       # API reference
│   ├── SETUP_GUIDE.md             # Setup instructions
│   ├── DEVELOPMENT_GUIDE.md       # Development guide
│   └── ai/                        # AI service docs (Future)
│
├── docker/                        # Docker configs
│   └── docker-compose.yml
│
├── .env                           # Environment variables
├── .env.example                   # Example env file
├── docker-compose.yml             # Main compose file
├── Makefile                       # Development commands
└── README.md                      # Project README
```

## 🔑 Các thành phần chính

### 1. Backend API (FastAPI)
- **Trạng thái**: 70% hoàn thành
- **Port**: 8000
- **Endpoints**: ~20 endpoints đã implement
- **Documentation**: Auto-generated Swagger UI tại `/docs`

### 2. Database (PostgreSQL)
- **Trạng thái**: 100% schema design
- **Port**: 5432
- **Tables**: 11 tables with relationships
- **Migrations**: Alembic configured

### 3. Authentication
- **Trạng thái**: 100% hoàn thành
- **Method**: JWT (JSON Web Tokens)
- **Token Types**: Access Token (30 min) + Refresh Token (7 days)
- **Password**: Bcrypt hashing

### 4. Authorization (RBAC)
- **Roles**: Admin, Instructor, Learner
- **Permissions**: Role-based access control
- **Implementation**: Decorator-based (@require_role)

### 5. Frontend (Next.js)
- **Trạng thái**: 0% - Chỉ có structure
- **Framework**: Next.js 14
- **UI Library**: shadcn/ui + Tailwind CSS (planned)

### 6. AI Services
- **Trạng thái**: 0% - Database models ready
- **Planned**: Chatbot, Analytics, Recommendations

## 📈 Roadmap

### Q1 2026 (Current)
- [x] Backend infrastructure setup
- [x] Database schema design
- [x] Authentication system
- [x] Core API endpoints (Auth, Users, Courses)
- [ ] Complete all API endpoints
- [ ] Service layer implementation
- [ ] Repository layer implementation
- [ ] Unit testing setup

### Q2 2026
- [ ] Frontend foundation (Next.js setup)
- [ ] Core UI components
- [ ] User dashboard
- [ ] Course browsing interface
- [ ] Video player integration
- [ ] Integration testing

### Q3 2026
- [ ] AI chatbot integration
- [ ] Analytics dashboard
- [ ] Recommendation system
- [ ] Performance optimization
- [ ] Mobile responsive design

### Q4 2026
- [ ] Production deployment
- [ ] Monitoring & logging
- [ ] Documentation finalization
- [ ] User training materials

## 🎯 Các vấn đề cần giải quyết

### High Priority
1. **Service Layer**: Tách business logic ra khỏi API routes
2. **Repository Layer**: Implement data access abstraction
3. **Testing**: Thêm unit tests và integration tests
4. **Missing Endpoints**: Lessons, Assignments, Submissions CRUD
5. **Frontend**: Bắt đầu implement components và pages

### Medium Priority
1. **Input Validation**: Thêm validators cho tất cả schemas
2. **Rate Limiting**: Implement API rate limiting
3. **Caching**: Redis integration cho performance
4. **File Upload**: Complete file handling system
5. **Email Service**: User verification và notifications

### Low Priority
1. **API Documentation**: Detailed endpoint documentation
2. **Code Quality**: Linting và formatting rules
3. **CI/CD Pipeline**: Automated testing và deployment
4. **Monitoring**: Application monitoring và logging

## 📚 Tài liệu tham khảo

1. [FastAPI Documentation](https://fastapi.tiangolo.com/)
2. [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
3. [PostgreSQL Documentation](https://www.postgresql.org/docs/)
4. [Next.js Documentation](https://nextjs.org/docs)
5. [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## 👥 Team & Roles

**Backend Development**: 1 developer (Main focus)
**Frontend Development**: Planned
**AI Integration**: Planned
**DevOps**: Using Docker Compose (basic setup complete)

## 📊 Metrics & KPIs

### Current Code Statistics
- **Backend Code**: ~2,500 lines
- **API Endpoints**: 20 implemented
- **Database Models**: 11 models
- **Test Coverage**: 0%
- **Documentation Coverage**: 30%

### Target Metrics
- **Test Coverage**: > 80%
- **API Response Time**: < 200ms (p95)
- **Database Queries**: Optimized with proper indexes
- **Code Quality**: Linting score > 9/10

---

**Cập nhật lần cuối**: 2026-03-29  
**Version**: 1.0.0-alpha
