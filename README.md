# AI-LMS - Learning Management System

A scalable Learning Management System built with FastAPI, Next.js, and PostgreSQL, with AI integration capability.

> 📚 **[Read Full Documentation](./docs/README.md)** | [Setup Guide](./docs/SETUP_GUIDE.md) | [API Docs](./docs/API_DOCUMENTATION.md) | [Development Guide](./docs/DEVELOPMENT_GUIDE.md)

## 🎯 Features

### Phase 1 (Current - MVP) ✅ 85% Complete
- ✅ User Management (Admin, Instructor, Learner roles)
- ✅ JWT Authentication & Authorization
- ✅ Course Management (CRUD operations)
- ✅ Lesson Management with video support
- ✅ Assignment & Submission system
- ✅ Progress tracking
- ✅ RESTful API with Swagger docs
- ✅ **Frontend with Next.js + shadcn/ui**

### Phase 2 (Planned)
- AI Assistant integration (LLM-powered)
- Video streaming optimization
- Analytics dashboard
- Notification system

## 🏗️ Architecture

```
AI-Support-for-Online-Teaching/
├── apps/
│   ├── backend/          # FastAPI Backend (Python 3.11)
│   └── frontend/         # Next.js 14 Frontend ✅
├── services/
│   └── ai/               # AI Service (future)
├── docker/               # Docker configs
├── docs/                 # Documentation
├── docker-compose.yml
├── Makefile
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AI-Support-for-Online-Teaching
make setup
```

### 2. Configure Environment

Edit `.env` file with your settings:

```bash
# Database
DB_USER=lms_user
DB_PASSWORD=your_secure_password
DB_NAME=lms_db

# Security
SECRET_KEY=your-secret-key-min-32-characters

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Start Backend Services

```bash
make start
```

Backend services will be available at:
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

### 4. Start Frontend (Development)

```bash
cd apps/frontend
npm install
npm run dev
```

Frontend will be available at:
- **Frontend**: http://localhost:3000

### 5. Run Migrations

```bash
make migration MESSAGE="initial migration"
make migrate
```

## 🎨 Frontend

### Tech Stack
- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn/ui + Tailwind CSS
- **State**: Zustand (auth) + React Query (server)
- **Forms**: React Hook Form + Zod
- **API**: Axios with interceptors

### Pages Available
| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Public landing page |
| Login | `/login` | User authentication |
| Register | `/register` | New user registration |
| Dashboard | `/dashboard` | Role-based dashboard |
| Courses | `/courses` | Browse all courses |
| Course Detail | `/courses/[slug]` | View course with lessons |
| Create Course | `/courses/create` | Instructor: create course |
| My Courses | `/courses/my` | Instructor: manage courses |
| Enrolled | `/courses/enrolled` | Learner: enrolled courses |
| Users | `/users` | Admin: user management |
| Profile | `/profile` | User profile settings |

### Frontend Commands

```bash
cd apps/frontend

# Development
npm run dev

# Build
npm run build

# Start production
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

## 📝 Documentation

### 📚 Complete Documentation
For detailed documentation, please visit the **[docs/](./docs/)** folder:

- **[Project Overview](./docs/PROJECT_OVERVIEW.md)** - Tổng quan dự án, tiến độ, roadmap
- **[Setup Guide](./docs/SETUP_GUIDE.md)** - Hướng dẫn cài đặt chi tiết
- **[Database Schema](./docs/DATABASE_SCHEMA.md)** - Chi tiết database structure
- **[API Documentation](./docs/API_DOCUMENTATION.md)** - API reference đầy đủ
- **[Development Guide](./docs/DEVELOPMENT_GUIDE.md)** - Coding standards & best practices

### 🔌 API Endpoints
Once the backend is running, interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Quick API Reference**:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login and get tokens |
| `/api/v1/auth/me` | GET | Get current user profile |
| `/api/v1/courses` | GET | List all courses |
| `/api/v1/courses` | POST | Create course (Instructor) |

> For complete API reference with examples, see **[API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md)**

## 🛠️ Development

### Available Commands

```bash
make help              # Show all available commands
make start             # Start all services
make stop              # Stop all services
make restart           # Restart services
make logs              # View all logs
make logs-backend      # View backend logs only
make migrate           # Run database migrations
make migration         # Create new migration
make shell-backend     # Open backend container shell
make shell-db          # Open database shell
make test              # Run tests
make lint              # Run linting
make format            # Format code
make clean             # Remove all containers and volumes
```

### Create Database Migration

```bash
make migration MESSAGE="add user avatar field"
make migrate
```

### Access Database

```bash
make shell-db
```

### View Logs

```bash
make logs-backend
```

## 📚 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.11) |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| Auth | JWT (python-jose) |
| Migrations | Alembic |
| Container | Docker & Docker Compose |
| Frontend | Next.js 14 ✅ |
| UI Library | shadcn/ui + Tailwind CSS ✅ |
| State Mgmt | Zustand + React Query ✅ |
| Forms | React Hook Form + Zod ✅ |

## 📊 Database Schema

```
users ──┬─→ courses ──┬─→ lessons ──→ materials
        │             │
        │             └─→ assignments ──→ submissions
        │
        └─→ enrollments ──→ lesson_progress
```

### Main Tables
- **users**: User accounts with roles
- **courses**: Course information
- **lessons**: Video lessons within courses
- **materials**: Additional learning materials
- **enrollments**: Course enrollments
- **lesson_progress**: User progress tracking
- **assignments**: Course assignments
- **submissions**: Student submissions
- **ai_conversations**: AI chat history (future)

## 🔐 User Roles & Permissions

| Permission | Admin | Instructor | Learner |
|------------|:-----:|:----------:|:-------:|
| Manage users | ✓ | ✗ | ✗ |
| Create courses | ✓ | ✓ | ✗ |
| Edit own courses | ✓ | ✓ | ✗ |
| View courses | ✓ | ✓ | ✓ (enrolled) |
| Create assignments | ✓ | ✓ | ✗ |
| Grade submissions | ✓ | ✓ | ✗ |
| Submit assignments | ✗ | ✗ | ✓ |
| Enroll in courses | ✗ | ✗ | ✓ |

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
cd apps/backend
pytest tests/test_auth.py -v
```

## 📖 Project Structure Details

### Backend (`apps/backend/`)

```
app/
├── core/           # Core configurations
│   ├── config.py       # Settings
│   ├── security.py     # JWT & password hashing
│   ├── dependencies.py # FastAPI dependencies
│   └── exceptions.py   # Custom exceptions
├── db/             # Database layer
│   ├── base.py         # SQLAlchemy Base
│   ├── session.py      # DB session factory
│   └── migrations/     # Alembic migrations
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic schemas
├── api/v1/         # API endpoints
│   ├── auth.py         # Authentication
│   ├── users.py        # User management
│   └── courses.py      # Course management
├── services/       # Business logic
├── repositories/   # Data access layer
└── utils/          # Utility functions
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Database connection error

```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db

# Check logs
make logs-backend
```

### Migration errors

```bash
# Reset database (⚠️ destroys data)
make clean
make start
make migratidon MESSAGE="initial"
make migrate
```

### Port already in use

Edit `.env` file and change ports:
```
BACKEND_PORT=8001
DB_PORT=5433
```

## 📞 Support & Resources

### 📖 Documentation
- **[Complete Documentation](./docs/README.md)** - Start here for all docs
- **[Setup Guide](./docs/SETUP_GUIDE.md)** - Installation and troubleshooting
- **[Development Guide](./docs/DEVELOPMENT_GUIDE.md)** - Contributing guidelines

### 🐛 Issues & Questions
For issues, questions, or feature requests:
- Check [Setup Guide Troubleshooting](./docs/SETUP_GUIDE.md#troubleshooting)
- Open a GitHub issue with detailed description
- Tag appropriately: `bug`, `feature`, `documentation`, `question`

### 📊 Project Status
- **Phase 1 (MVP)**: ~85% Complete ✅
- **Backend**: 49 API endpoints implemented
- **Frontend**: Core pages complete with Next.js 14
- **Next Phase**: AI integration, analytics

See [PROGRESS_TRACKING.md](./PROGRESS_TRACKING.md) for detailed progress tracking.

---

**Built with ❤️ for online education**  
**Version**: 1.0.0-beta | **Last Updated**: 2026-03-29