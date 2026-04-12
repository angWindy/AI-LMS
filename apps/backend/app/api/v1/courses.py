"""
Course management API endpoints.
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from slugify import slugify

from app.core.dependencies import DBSession, CurrentUser, InstructorUser, get_current_user_optional
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.models.material import Material
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.lesson import MaterialResponse
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
)
from app.schemas.common import PaginatedResponse, Message
from app.utils.file_handler import file_handler

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


def check_course_owner(db: DBSession, course_id: uuid.UUID, user: User) -> Course:
    """Check if user owns the course or is admin."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return course


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
        # If previously dropped, re-activate enrollment
        if existing.status == EnrollmentStatus.DROPPED:
            existing.status = EnrollmentStatus.ACTIVE
            existing.enrolled_at = datetime.now(timezone.utc)
            db.commit()
            return Message(message="Successfully re-enrolled in course")
        else:
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


@router.post("/{course_id}/unenroll", response_model=Message)
async def unenroll_from_course(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Unenroll current user from a course."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    # Check if enrolled
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id,
        Enrollment.status == EnrollmentStatus.ACTIVE,
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )

    # Update status to DROPPED instead of deleting
    enrollment.status = EnrollmentStatus.DROPPED
    db.commit()

    return Message(message="Successfully unenrolled from course")


@router.get("/{course_id}/enrollment-status")
async def get_enrollment_status(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get current user's enrollment status for a course."""
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id,
    ).first()

    if not enrollment:
        return {"enrolled": False, "status": None}

    return {
        "enrolled": enrollment.status == EnrollmentStatus.ACTIVE,
        "status": enrollment.status.value,
        "enrolled_at": enrollment.enrolled_at,
        "progress": enrollment.progress,
    }


@router.get("/{course_id}/lessons", response_model=List)
async def get_course_lessons(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get all lessons for a course.
    
    For instructors/admins: returns all lessons
    For others: returns only published lessons
    """
    from app.schemas.lesson import LessonResponse

    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        raise NotFoundException("Course not found")

    # Check if user is instructor or admin
    is_owner = current_user and (
        current_user.role == UserRole.ADMIN or 
        course.instructor_id == current_user.id
    )
    
    query = db.query(Lesson).filter(Lesson.course_id == course_id)
    
    # Only show published lessons for non-owners
    if not is_owner:
        query = query.filter(Lesson.is_published == True)
    
    lessons = query.order_by(Lesson.order_index).all()

    return [LessonResponse.model_validate(lesson) for lesson in lessons]


@router.get("/{course_id}/materials", response_model=List[MaterialResponse])
async def get_course_materials(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get materials attached directly to a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    is_owner = current_user and (
        current_user.role == UserRole.ADMIN or
        course.instructor_id == current_user.id
    )

    if not is_owner:
        if not current_user:
            raise ForbiddenException("You must login to access course materials")

        is_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.user_id == current_user.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        ).first() is not None
        if not is_enrolled:
            raise ForbiddenException("You must be enrolled in this course")

    return db.query(Material).filter(
        Material.course_id == course_id,
        Material.lesson_id.is_(None),
    ).order_by(Material.order_index).all()


@router.post("/{course_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_course_material(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: InstructorUser,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    material_type: str = Form(..., alias="type"),
    file: Optional[UploadFile] = File(None),
    external_url: Optional[str] = Form(None),
):
    """Create a material directly under a course."""
    check_course_owner(db, course_id, current_user)

    max_order = db.query(func.max(Material.order_index)).filter(
        Material.course_id == course_id,
        Material.lesson_id.is_(None),
    ).scalar()
    next_order = (max_order or 0) + 1

    file_url = external_url
    file_size = None
    mime_type = None

    if file and file.filename:
        file_info = await file_handler.save_file(
            file,
            subdirectory=f"materials/courses/{course_id}",
            allowed_types=file_handler.ALLOWED_VIDEO_TYPES + file_handler.ALLOWED_DOCUMENT_TYPES + file_handler.ALLOWED_IMAGE_TYPES,
        )
        file_url = file_info["file_url"]
        file_size = file_info["file_size"]
        mime_type = file_info["mime_type"]

    material = Material(
        course_id=course_id,
        lesson_id=None,
        title=title,
        description=description,
        type=material_type,
        file_url=file_url,
        file_size=file_size,
        mime_type=mime_type,
        order_index=next_order,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    return material


@router.delete("/materials/{material_id}", response_model=Message)
async def delete_course_material(
    material_id: uuid.UUID,
    db: DBSession,
    current_user: InstructorUser,
):
    """Delete a course-level material."""
    material = db.query(Material).options(joinedload(Material.course)).filter(
        Material.id == material_id,
        Material.lesson_id.is_(None),
    ).first()
    if not material:
        raise NotFoundException("Course material not found")

    if current_user.role != UserRole.ADMIN and material.course.instructor_id != current_user.id:
        raise ForbiddenException("Only course instructor or admin can delete this material")

    if material.file_url:
        file_handler.delete_file(material.file_url)

    db.delete(material)
    db.commit()

    return Message(message="Course material deleted successfully")


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
