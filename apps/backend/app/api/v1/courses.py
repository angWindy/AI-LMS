"""
Course management API endpoints.
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import func
from slugify import slugify

from app.core.dependencies import DBSession, CurrentUser, InstructorUser
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
)
from app.schemas.common import PaginatedResponse, Message

router = APIRouter(prefix="/courses", tags=["Courses"])


def generate_unique_slug(db: DBSession, title: str, exclude_id: uuid.UUID | None = None) -> str:
    """Generate a unique slug for a course."""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1

    while True:
        query = db.query(Course).filter(Course.slug == slug)
        if exclude_id:
            query = query.filter(Course.id != exclude_id)
        existing = query.first()
        if not existing:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=PaginatedResponse[CourseListResponse])
async def list_courses(
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CourseStatus] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
):
    """List all published courses with filtering and pagination."""
    query = db.query(Course).filter(Course.status == CourseStatus.PUBLISHED)

    if category:
        query = query.filter(Course.category == category)
    if level:
        query = query.filter(Course.level == level)
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    courses = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for course in courses:
        lesson_count = db.query(func.count(Lesson.id)).filter(
            Lesson.course_id == course.id,
            Lesson.is_published == True
        ).scalar()
        enrollment_count = db.query(func.count(Enrollment.id)).filter(
            Enrollment.course_id == course.id
        ).scalar()

        items.append(CourseListResponse(
            id=course.id,
            title=course.title,
            slug=course.slug,
            short_description=course.short_description,
            thumbnail_url=course.thumbnail_url,
            status=course.status,
            level=course.level,
            instructor=course.instructor,
            lesson_count=lesson_count,
            enrollment_count=enrollment_count,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: DBSession,
    current_user: InstructorUser,
):
    """Create a new course (Instructor or Admin only)."""
    slug = generate_unique_slug(db, course_data.title)

    course = Course(
        instructor_id=current_user.id,
        title=course_data.title,
        slug=slug,
        description=course_data.description,
        short_description=course_data.short_description,
        category=course_data.category,
        level=course_data.level,
        language=course_data.language,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: uuid.UUID,
    db: DBSession,
):
    """Get course details by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    lesson_count = db.query(func.count(Lesson.id)).filter(
        Lesson.course_id == course.id,
        Lesson.is_published == True
    ).scalar()
    enrollment_count = db.query(func.count(Enrollment.id)).filter(
        Enrollment.course_id == course.id
    ).scalar()

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        short_description=course.short_description,
        thumbnail_url=course.thumbnail_url,
        status=course.status,
        category=course.category,
        level=course.level,
        language=course.language,
        estimated_duration=course.estimated_duration,
        is_featured=course.is_featured,
        created_at=course.created_at,
        updated_at=course.updated_at,
        published_at=course.published_at,
        instructor_id=course.instructor_id,
        instructor=course.instructor,
        lesson_count=lesson_count,
        enrollment_count=enrollment_count,
    )


@router.get("/slug/{slug}", response_model=CourseDetailResponse)
async def get_course_by_slug(
    slug: str,
    db: DBSession,
):
    """Get course details by slug."""
    course = db.query(Course).filter(Course.slug == slug).first()

    if not course:
        raise NotFoundException("Course not found")

    lesson_count = db.query(func.count(Lesson.id)).filter(
        Lesson.course_id == course.id,
        Lesson.is_published == True
    ).scalar()
    enrollment_count = db.query(func.count(Enrollment.id)).filter(
        Enrollment.course_id == course.id
    ).scalar()

    return CourseDetailResponse(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        short_description=course.short_description,
        thumbnail_url=course.thumbnail_url,
        status=course.status,
        category=course.category,
        level=course.level,
        language=course.language,
        estimated_duration=course.estimated_duration,
        is_featured=course.is_featured,
        created_at=course.created_at,
        updated_at=course.updated_at,
        published_at=course.published_at,
        instructor_id=course.instructor_id,
        instructor=course.instructor,
        lesson_count=lesson_count,
        enrollment_count=enrollment_count,
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    course_data: CourseUpdate,
    db: DBSession,
    current_user: InstructorUser,
):
    """Update a course (owner or admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    # Check permission
    if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
        raise ForbiddenException("You don't have permission to edit this course")

    # Update fields
    if course_data.title is not None:
        course.title = course_data.title
        course.slug = generate_unique_slug(db, course_data.title, exclude_id=course_id)
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.short_description is not None:
        course.short_description = course_data.short_description
    if course_data.category is not None:
        course.category = course_data.category
    if course_data.level is not None:
        course.level = course_data.level
    if course_data.language is not None:
        course.language = course_data.language
    if course_data.thumbnail_url is not None:
        course.thumbnail_url = course_data.thumbnail_url

    db.commit()
    db.refresh(course)

    return course


@router.delete("/{course_id}", response_model=Message)
async def delete_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: InstructorUser,
):
    """Delete a course (owner or admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    # Check permission
    if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
        raise ForbiddenException("You don't have permission to delete this course")

    db.delete(course)
    db.commit()

    return Message(message="Course deleted successfully")


@router.post("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: InstructorUser,
):
    """Publish a course (owner or admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
        raise ForbiddenException("You don't have permission to publish this course")

    course.status = CourseStatus.PUBLISHED
    course.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(course)

    return course


@router.post("/{course_id}/archive", response_model=CourseResponse)
async def archive_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: InstructorUser,
):
    """Archive a course (owner or admin only)."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
        raise ForbiddenException("You don't have permission to archive this course")

    course.status = CourseStatus.ARCHIVED

    db.commit()
    db.refresh(course)

    return course


@router.post("/{course_id}/enroll", response_model=Message)
async def enroll_in_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Enroll current user in a course."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    if course.status != CourseStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enroll in unpublished course"
        )

    # Check if already enrolled
    existing = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this course"
        )

    enrollment = Enrollment(
        user_id=current_user.id,
        course_id=course_id,
    )

    db.add(enrollment)
    db.commit()

    return Message(message="Successfully enrolled in course")


@router.get("/{course_id}/lessons", response_model=List)
async def get_course_lessons(
    course_id: uuid.UUID,
    db: DBSession,
):
    """Get all lessons for a course."""
    from app.schemas.lesson import LessonResponse

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    lessons = db.query(Lesson).filter(
        Lesson.course_id == course_id,
        Lesson.is_published == True,
    ).order_by(Lesson.order_index).all()

    return [LessonResponse.model_validate(lesson) for lesson in lessons]


@router.get("/my/teaching", response_model=List[CourseResponse])
async def get_my_teaching_courses(
    db: DBSession,
    current_user: InstructorUser,
):
    """Get courses created by the current instructor."""
    courses = db.query(Course).filter(
        Course.instructor_id == current_user.id
    ).order_by(Course.created_at.desc()).all()

    return courses


@router.get("/my/enrolled", response_model=List[CourseListResponse])
async def get_my_enrolled_courses(
    db: DBSession,
    current_user: CurrentUser,
):
    """Get courses the current user is enrolled in."""
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.status == EnrollmentStatus.ACTIVE,
    ).all()

    items = []
    for enrollment in enrollments:
        course = enrollment.course
        lesson_count = db.query(func.count(Lesson.id)).filter(
            Lesson.course_id == course.id,
            Lesson.is_published == True
        ).scalar()
        enrollment_count = db.query(func.count(Enrollment.id)).filter(
            Enrollment.course_id == course.id
        ).scalar()

        items.append(CourseListResponse(
            id=course.id,
            title=course.title,
            slug=course.slug,
            short_description=course.short_description,
            thumbnail_url=course.thumbnail_url,
            status=course.status,
            level=course.level,
            instructor=course.instructor,
            lesson_count=lesson_count,
            enrollment_count=enrollment_count,
        ))

    return items
