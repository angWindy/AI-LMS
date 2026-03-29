# Development Guide - AI-LMS

Hướng dẫn phát triển cho developers tham gia dự án AI-LMS.

## Mục lục

1. [Coding Standards](#coding-standards)
2. [Project Architecture](#project-architecture)
3. [Adding New Features](#adding-new-features)
4. [Database Migrations](#database-migrations)
5. [Testing](#testing)
6. [API Development](#api-development)
7. [Common Tasks](#common-tasks)
8. [Best Practices](#best-practices)
9. [Debugging](#debugging)

---

## Coding Standards

### Python Code Style

Dự án tuân theo **PEP 8** với một số customizations.

#### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

# Functions/Methods: snake_case
def get_user_by_email(email: str):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 104857600

# Private methods: _snake_case
def _internal_helper():
    pass

# Variables: snake_case
user_email = "test@example.com"
```

#### Type Hints

**ALWAYS use type hints** cho functions và methods:

```python
from typing import List, Optional
from uuid import UUID

def get_courses(
    instructor_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 10
) -> List[Course]:
    """Get list of courses with pagination."""
    pass
```

#### Docstrings

Sử dụng Google-style docstrings:

```python
def create_course(
    title: str,
    instructor_id: UUID,
    description: Optional[str] = None
) -> Course:
    """
    Create a new course.
    
    Args:
        title: Course title
        instructor_id: ID of the instructor creating the course
        description: Optional course description
        
    Returns:
        Created Course object
        
    Raises:
        ValueError: If title is empty
        ForbiddenException: If instructor_id is invalid
        
    Example:
        >>> course = create_course("Python 101", instructor_uuid)
        >>> print(course.title)
        'Python 101'
    """
    pass
```

#### Code Formatting

```bash
# Install development tools
pip install -r requirements-dev.txt

# Format code with Black
black app/

# Check with flake8
flake8 app/

# Sort imports with isort
isort app/

# Type checking with mypy (optional)
mypy app/
```

### File Organization

```python
# File header (optional but recommended for complex files)
"""
Module: app/services/course_service.py
Description: Business logic for course management
Author: Your Name
Created: 2026-03-29
"""

# Imports order:
# 1. Standard library
import os
from datetime import datetime
from typing import List, Optional

# 2. Third-party
from fastapi import HTTPException
from sqlalchemy.orm import Session

# 3. Local application
from app.models.course import Course
from app.schemas.course import CourseCreate
from app.core.exceptions import NotFoundException
```

---

## Project Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│         API Layer (Routes)          │  ← FastAPI endpoints
│  - Request validation (Pydantic)    │
│  - Response formatting              │
│  - Authentication/Authorization     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│       Service Layer (Business)      │  ← Business logic
│  - Domain rules                     │
│  - Transactions                     │
│  - Orchestration                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     Repository Layer (Data)         │  ← Data access
│  - Database queries                 │
│  - Data mapping                     │
│  - Query builders                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│        Model Layer (ORM)            │  ← Database models
│  - SQLAlchemy models                │
│  - Relationships                    │
└─────────────────────────────────────┘
```

### Current vs Target Architecture

**Current (MVP):**
```
API Routes → Database Models (direct)
```

**Target:**
```
API Routes → Services → Repositories → Models
```

---

## Adding New Features

### Step-by-Step Guide

#### 1. Create Database Model

**Location**: `apps/backend/app/models/`

**Example**: Adding a "Quiz" feature

```python
# app/models/quiz.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
import uuid

class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    time_limit_minutes = Column(Integer)  # null = no limit
    passing_score = Column(Integer, default=70)
    is_published = Column(Boolean, default=False)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # multiple_choice, true_false, short_answer
    points = Column(Integer, default=1)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
```

**Update related models**:
```python
# In app/models/lesson.py
class Lesson(Base, TimestampMixin):
    # ... existing code ...
    quizzes = relationship("Quiz", back_populates="lesson")
```

#### 2. Create Pydantic Schemas

**Location**: `apps/backend/app/schemas/`

```python
# app/schemas/quiz.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request schemas
class QuizQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000)
    question_type: str = Field(..., pattern="^(multiple_choice|true_false|short_answer)$")
    points: int = Field(default=1, ge=1, le=100)
    order_index: int = Field(..., ge=0)

class QuizCreate(BaseModel):
    lesson_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=180)
    passing_score: int = Field(default=70, ge=0, le=100)
    questions: List[QuizQuestionCreate] = []

class QuizUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=180)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    is_published: Optional[bool] = None

# Response schemas
class QuizQuestionResponse(BaseModel):
    id: str
    quiz_id: str
    question_text: str
    question_type: str
    points: int
    order_index: int
    
    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    description: Optional[str]
    time_limit_minutes: Optional[int]
    passing_score: int
    is_published: bool
    question_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 3. Create Repository (Target Architecture)

**Location**: `apps/backend/app/repositories/`

```python
# app/repositories/quiz_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.quiz import Quiz, QuizQuestion

class QuizRepository:
    """Data access layer for Quiz operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, quiz_data: dict) -> Quiz:
        """Create new quiz."""
        quiz = Quiz(**quiz_data)
        self.db.add(quiz)
        self.db.commit()
        self.db.refresh(quiz)
        return quiz
    
    def get_by_id(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID."""
        return self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    def get_by_lesson(self, lesson_id: str) -> List[Quiz]:
        """Get all quizzes for a lesson."""
        return self.db.query(Quiz).filter(Quiz.lesson_id == lesson_id).all()
    
    def update(self, quiz_id: str, update_data: dict) -> Optional[Quiz]:
        """Update quiz."""
        quiz = self.get_by_id(quiz_id)
        if quiz:
            for key, value in update_data.items():
                setattr(quiz, key, value)
            self.db.commit()
            self.db.refresh(quiz)
        return quiz
    
    def delete(self, quiz_id: str) -> bool:
        """Delete quiz."""
        quiz = self.get_by_id(quiz_id)
        if quiz:
            self.db.delete(quiz)
            self.db.commit()
            return True
        return False
```

#### 4. Create Service Layer (Target Architecture)

**Location**: `apps/backend/app/services/`

```python
# app/services/quiz_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.quiz import Quiz
from app.schemas.quiz import QuizCreate, QuizUpdate
from app.repositories.quiz_repository import QuizRepository
from app.core.exceptions import NotFoundException, ForbiddenException

class QuizService:
    """Business logic for quiz management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = QuizRepository(db)
    
    def create_quiz(self, quiz_data: QuizCreate, instructor_id: str) -> Quiz:
        """
        Create a new quiz.
        
        Validates:
        - Lesson exists
        - Instructor owns the course
        - Questions are valid
        """
        # Validate lesson ownership
        lesson = self._validate_lesson_access(quiz_data.lesson_id, instructor_id)
        
        # Create quiz
        quiz_dict = quiz_data.model_dump(exclude={'questions'})
        quiz = self.repository.create(quiz_dict)
        
        # Create questions
        for question_data in quiz_data.questions:
            self._create_question(quiz.id, question_data)
        
        return quiz
    
    def get_quiz(self, quiz_id: str) -> Quiz:
        """Get quiz by ID."""
        quiz = self.repository.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundException(f"Quiz {quiz_id} not found")
        return quiz
    
    def update_quiz(self, quiz_id: str, update_data: QuizUpdate, user_id: str) -> Quiz:
        """Update quiz (instructor only)."""
        quiz = self.get_quiz(quiz_id)
        
        # Validate ownership
        self._validate_lesson_access(quiz.lesson_id, user_id)
        
        # Update
        update_dict = update_data.model_dump(exclude_unset=True)
        quiz = self.repository.update(quiz_id, update_dict)
        return quiz
    
    def delete_quiz(self, quiz_id: str, user_id: str) -> None:
        """Delete quiz (instructor only)."""
        quiz = self.get_quiz(quiz_id)
        self._validate_lesson_access(quiz.lesson_id, user_id)
        self.repository.delete(quiz_id)
    
    def _validate_lesson_access(self, lesson_id: str, user_id: str):
        """Validate that user owns the course containing this lesson."""
        # Implementation...
        pass
    
    def _create_question(self, quiz_id: str, question_data):
        """Create quiz question."""
        # Implementation...
        pass
```

#### 5. Create API Endpoints

**Location**: `apps/backend/app/api/v1/`

```python
# app/api/v1/quizzes.py
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(
    quiz_data: QuizCreate,
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Create a new quiz.
    
    - **Requires**: INSTRUCTOR or ADMIN role
    - **Validates**: Lesson ownership
    """
    service = QuizService(db)
    quiz = service.create_quiz(quiz_data, current_user.id)
    return quiz

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz by ID."""
    service = QuizService(db)
    quiz = service.get_quiz(quiz_id)
    return quiz

@router.put("/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: str,
    update_data: QuizUpdate,
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update quiz."""
    service = QuizService(db)
    quiz = service.update_quiz(quiz_id, update_data, current_user.id)
    return quiz

@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: str,
    current_user: User = Depends(require_role([UserRole.INSTRUCTOR, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete quiz."""
    service = QuizService(db)
    service.delete_quiz(quiz_id, current_user.id)
```

**Register router**:
```python
# In app/api/v1/router.py
from app.api.v1 import auth, users, courses, quizzes

api_router.include_router(quizzes.router)
```

#### 6. Create Database Migration

```bash
# Create migration
make migration MESSAGE="add quiz tables"

# Review the generated migration file in:
# apps/backend/app/db/migrations/versions/

# Apply migration
make migrate
```

#### 7. Write Tests

**Location**: `apps/backend/tests/`

```python
# tests/test_quiz_service.py
import pytest
from app.services.quiz_service import QuizService
from app.schemas.quiz import QuizCreate, QuizQuestionCreate

def test_create_quiz(db_session, test_instructor, test_lesson):
    """Test quiz creation."""
    service = QuizService(db_session)
    
    quiz_data = QuizCreate(
        lesson_id=test_lesson.id,
        title="Python Basics Quiz",
        description="Test your knowledge",
        time_limit_minutes=30,
        passing_score=70,
        questions=[
            QuizQuestionCreate(
                question_text="What is Python?",
                question_type="multiple_choice",
                points=2,
                order_index=0
            )
        ]
    )
    
    quiz = service.create_quiz(quiz_data, test_instructor.id)
    
    assert quiz.title == "Python Basics Quiz"
    assert len(quiz.questions) == 1
    assert quiz.lesson_id == test_lesson.id

def test_create_quiz_unauthorized(db_session, test_learner, test_lesson):
    """Test that learner cannot create quiz."""
    service = QuizService(db_session)
    
    quiz_data = QuizCreate(
        lesson_id=test_lesson.id,
        title="Unauthorized Quiz"
    )
    
    with pytest.raises(ForbiddenException):
        service.create_quiz(quiz_data, test_learner.id)
```

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
make migration MESSAGE="add quiz feature"

# Manual migration (for data migrations)
docker-compose exec backend alembic revision -m "seed initial data"
```

### Migration File Structure

```python
"""add quiz feature

Revision ID: abc123def456
Revises: 299a7a8507ce
Create Date: 2026-03-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = '299a7a8507ce'
branch_labels = None
depends_on = None

def upgrade():
    """Apply migration."""
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lesson_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        # ... more columns
    )
    
    # Create indexes
    op.create_index('ix_quizzes_lesson_id', 'quizzes', ['lesson_id'])

def downgrade():
    """Revert migration."""
    op.drop_index('ix_quizzes_lesson_id')
    op.drop_table('quizzes')
```

### Migration Best Practices

1. **Always review** auto-generated migrations
2. **Test migrations** on development database first
3. **Write reversible migrations** (implement downgrade)
4. **One logical change per migration**
5. **Add indexes** for foreign keys and frequently queried columns
6. **Use batch operations** for large data migrations

---

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── test_auth.py             # Auth tests
├── test_users.py            # User management tests
├── test_courses.py          # Course tests
└── test_quiz_service.py     # Quiz service tests
```

### Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User, UserRole

@pytest.fixture
def db_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_admin(db_session):
    """Create test admin user."""
    user = User(
        email="admin@test.com",
        password_hash="hashed",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_quiz_service.py -v

# Run with coverage
pytest --cov=app tests/

# Run with specific marker
pytest -m "unit" tests/
```

---

## API Development

### Request/Response Flow

```
Client Request
     ↓
FastAPI Route Handler
     ↓
Dependency Injection (auth, db)
     ↓
Request Validation (Pydantic)
     ↓
Service Layer (business logic)
     ↓
Repository Layer (data access)
     ↓
Database (PostgreSQL)
     ↓
Response Formatting (Pydantic)
     ↓
Client Response
```

### Error Handling

```python
# Use custom exceptions
from app.core.exceptions import NotFoundException, ForbiddenException

# In service
def get_course(self, course_id: str) -> Course:
    course = self.repository.get_by_id(course_id)
    if not course:
        raise NotFoundException(f"Course {course_id} not found")
    return course

# Custom exception classes automatically return proper HTTP status
```

---

## Common Tasks

### Add a New Endpoint

1. Define Pydantic schemas
2. Create repository method (if needed)
3. Create service method
4. Create API route
5. Add tests
6. Update API documentation

### Add a New Model

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create migration
4. Apply migration
5. Create schemas
6. Create repository/service
7. Add tests

### Update Existing Feature

1. Update model (if schema changes)
2. Create migration (if schema changes)
3. Update schemas
4. Update service logic
5. Update tests
6. Update API documentation

---

## Best Practices

### 1. Always Use Transactions

```python
# Good: Transaction handled by service
def create_course_with_lessons(course_data, lessons_data):
    try:
        course = create_course(course_data)
        for lesson_data in lessons_data:
            create_lesson(lesson_data, course.id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise
```

### 2. Validate Early

```python
# Validate in schemas, not in business logic
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
```

### 3. Use Dependency Injection

```python
# Good: Dependencies injected
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = CourseService(db)
    return service.create_course(course_data, current_user.id)
```

### 4. Return Proper Status Codes

```python
@router.post("/", status_code=status.HTTP_201_CREATED)  # 201 for creation
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)  # 204 for deletion
@router.get("/")  # 200 is default
```

---

## Debugging

### Enable Debug Logs

```python
# In app/core/config.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use in code
logger.debug(f"Creating course: {course_data}")
logger.info(f"Course created: {course.id}")
logger.error(f"Error: {str(e)}")
```

### Debug in VS Code

```json
// .vscode/launch.json
{
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/apps/backend"
    }
  ]
}
```

### Database Debugging

```bash
# Check query logs
docker-compose logs -f db

# Check active connections
make shell-db
SELECT * FROM pg_stat_activity;

# Explain query
EXPLAIN ANALYZE SELECT * FROM courses WHERE instructor_id = 'xxx';
```

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-quiz-system

# Make changes and commit
git add .
git commit -m "feat: add quiz system with questions"

# Push and create PR
git push origin feature/add-quiz-system
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/tooling changes

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-29
