"""
Export all schemas.
"""
from app.schemas.common import (
    Message,
    PaginationParams,
    PaginatedResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    PasswordChange,
)
from app.schemas.course import (
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
)
from app.schemas.lesson import (
    LessonBase,
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    LessonDetailResponse,
    LessonProgressUpdate,
    LessonProgressResponse,
    MaterialCreate,
    MaterialResponse,
)
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentQuestionCreate,
    AssignmentQuestionResponse,
    AssignmentOptionCreate,
    AssignmentOptionResponse,
)

__all__ = [
    "Message",
    "PaginationParams",
    "PaginatedResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "PasswordChange",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CourseDetailResponse",
    "LessonBase",
    "LessonCreate",
    "LessonUpdate",
    "LessonResponse",
    "LessonDetailResponse",
    "LessonProgressUpdate",
    "LessonProgressResponse",
    "MaterialCreate",
    "MaterialResponse",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentResponse",
    "AssignmentQuestionCreate",
    "AssignmentQuestionResponse",
    "AssignmentOptionCreate",
    "AssignmentOptionResponse",
]
