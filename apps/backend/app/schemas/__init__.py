"""
Export all schemas.
"""
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentOptionCreate,
    AssignmentOptionResponse,
    AssignmentQuestionCreate,
    AssignmentQuestionResponse,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.common import (
    Message,
    PaginatedResponse,
    PaginationParams,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.course import (
    CourseBase,
    CourseCreate,
    CourseDetailResponse,
    CourseResponse,
    CourseUpdate,
)
from app.schemas.lesson import (
    LessonBase,
    LessonCreate,
    LessonDetailResponse,
    LessonProgressResponse,
    LessonProgressUpdate,
    LessonResponse,
    LessonUpdate,
    MaterialCreate,
    MaterialResponse,
)
from app.schemas.slide_deck import (
    SlideDeckGenerateDraftRequest,
    SlideDeckResponse,
)
from app.schemas.user import (
    PasswordChange,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
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
    "SlideDeckGenerateDraftRequest",
    "SlideDeckResponse",
]
