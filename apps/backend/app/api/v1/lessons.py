"""
Lesson management API endpoints.
"""
from typing import List, Optional
import uuid

from fastapi import APIRouter, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import DBSession, CurrentUser, InstructorUser
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.material import Material
from app.models.lesson_progress import LessonProgress
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonOrderUpdate,
    LessonResponse,
    LessonDetailResponse,
    LessonProgressUpdate,
    LessonProgressResponse,
    MaterialCreate,
    MaterialResponse,
)
from app.schemas.common import Message
from app.utils.file_handler import file_handler

router = APIRouter(prefix="/lessons", tags=["Lessons"])


def check_course_access(db: DBSession, course_id: uuid.UUID, user: User, require_owner: bool = False):
    """Check if user has access to the course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")
    
    if require_owner:
        if user.role != UserRole.ADMIN and course.instructor_id != user.id:
            raise ForbiddenException("Only course instructor or admin can perform this action")
    
    return course


def check_lesson_access(db: DBSession, lesson_id: uuid.UUID, user: User, require_owner: bool = False):
    """Check if user has access to the lesson's course."""
    lesson = db.query(Lesson).options(joinedload(Lesson.course)).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    if require_owner:
        if user.role != UserRole.ADMIN and lesson.course.instructor_id != user.id:
            raise ForbiddenException("Only course instructor or admin can perform this action")
    
    return lesson


# ============ LESSON CRUD ============

@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    lesson_data: LessonCreate,
):
    """Create a new lesson in a course."""
    # Check course access
    course = check_course_access(db, course_id, current_user, require_owner=True)
    
    # Get next order index
    max_order = db.query(func.max(Lesson.order_index)).filter(Lesson.course_id == course_id).scalar()
    next_order = (max_order or 0) + 1
    
    # Create lesson
    lesson = Lesson(
        course_id=course_id,
        title=lesson_data.title,
        description=lesson_data.description,
        content=lesson_data.content,
        order_index=lesson_data.order_index or next_order,
        is_preview=lesson_data.is_preview,
    )
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return lesson


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get lesson details with materials."""
    lesson = db.query(Lesson).options(
        joinedload(Lesson.materials),
        joinedload(Lesson.course)
    ).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    # Check access: admin, instructor, or enrolled student (or preview lesson)
    if not lesson.is_preview:
        is_admin = current_user.role == UserRole.ADMIN
        is_instructor = lesson.course.instructor_id == current_user.id
        is_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == lesson.course_id,
            Enrollment.user_id == current_user.id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        ).first() is not None
        
        if not (is_admin or is_instructor or is_enrolled):
            raise ForbiddenException("You must be enrolled in this course to access this lesson")
    
    return lesson


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    lesson_data: LessonUpdate,
    current_user: InstructorUser,
):
    """Update a lesson."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    # Update fields
    update_data = lesson_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)
    
    db.commit()
    db.refresh(lesson)
    
    return lesson


@router.delete("/{lesson_id}", response_model=Message)
async def delete_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete a lesson and its materials."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    # Delete associated materials' files
    for material in lesson.materials:
        if material.file_url:
            file_handler.delete_file(material.file_url)
    
    # Delete lesson (cascades to materials)
    db.delete(lesson)
    db.commit()
    
    return Message(message="Lesson deleted successfully")


@router.patch("/{lesson_id}/order", response_model=LessonResponse)
async def update_lesson_order(
    db: DBSession,
    lesson_id: uuid.UUID,
    order_data: LessonOrderUpdate,
    current_user: InstructorUser,
):
    """Update lesson order within a course."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    lesson.order_index = order_data.order_index
    db.commit()
    db.refresh(lesson)
    
    return lesson


@router.post("/{lesson_id}/publish", response_model=LessonResponse)
async def publish_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Publish a lesson."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    lesson.is_published = True
    db.commit()
    db.refresh(lesson)
    
    return lesson


# ============ MATERIALS ============

@router.post("/{lesson_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    material_type: str = Form(..., alias="type"),
    file: Optional[UploadFile] = File(None),
    external_url: Optional[str] = Form(None),
):
    """Create a material for a lesson with optional file upload."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    # Get next order index
    max_order = db.query(func.max(Material.order_index)).filter(Material.lesson_id == lesson_id).scalar()
    next_order = (max_order or 0) + 1
    
    # Initialize file info
    file_url = external_url
    file_size = None
    mime_type = None
    
    # Handle file upload
    if file and file.filename:
        file_info = await file_handler.save_material_file(file, str(lesson_id))
        file_url = file_info["file_url"]
        file_size = file_info["file_size"]
        mime_type = file_info["mime_type"]
    
    # Create material
    material = Material(
        lesson_id=lesson_id,
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


@router.get("/{lesson_id}/materials", response_model=List[MaterialResponse])
async def list_materials(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: CurrentUser,
):
    """List all materials for a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    materials = db.query(Material).filter(
        Material.lesson_id == lesson_id
    ).order_by(Material.order_index).all()
    
    return materials


@router.delete("/materials/{material_id}", response_model=Message)
async def delete_material(
    db: DBSession,
    material_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete a material."""
    material = db.query(Material).options(
        joinedload(Material.lesson).joinedload(Lesson.course)
    ).filter(Material.id == material_id).first()
    
    if not material:
        raise NotFoundException("Material not found")
    
    # Check ownership
    if current_user.role != UserRole.ADMIN and material.lesson.course.instructor_id != current_user.id:
        raise ForbiddenException("Only course instructor or admin can delete this material")
    
    # Delete file if exists
    if material.file_url:
        file_handler.delete_file(material.file_url)
    
    db.delete(material)
    db.commit()
    
    return Message(message="Material deleted successfully")


# ============ LESSON PROGRESS ============

@router.post("/{lesson_id}/progress", response_model=LessonProgressResponse)
async def update_progress(
    db: DBSession,
    lesson_id: uuid.UUID,
    progress_data: LessonProgressUpdate,
    current_user: CurrentUser,
):
    """Update or create lesson progress for current user."""
    # Verify lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    # Check if user is enrolled
    enrollment = db.query(Enrollment).filter(
        Enrollment.course_id == lesson.course_id,
        Enrollment.user_id == current_user.id,
        Enrollment.status == EnrollmentStatus.ACTIVE
    ).first()
    
    if not enrollment and current_user.role not in [UserRole.ADMIN, UserRole.INSTRUCTOR]:
        raise ForbiddenException("You must be enrolled to track progress")
    
    # Get or create progress
    progress = db.query(LessonProgress).filter(
        LessonProgress.lesson_id == lesson_id,
        LessonProgress.user_id == current_user.id
    ).first()
    
    if progress:
        # Update existing
        progress.watched_seconds = progress_data.watched_seconds
        progress.last_position = progress_data.last_position
        progress.is_completed = progress_data.is_completed
    else:
        # Create new
        progress = LessonProgress(
            lesson_id=lesson_id,
            user_id=current_user.id,
            watched_seconds=progress_data.watched_seconds,
            last_position=progress_data.last_position,
            is_completed=progress_data.is_completed,
        )
        db.add(progress)
    
    db.commit()
    db.refresh(progress)
    
    # Add total_seconds from lesson video
    result = LessonProgressResponse(
        lesson_id=progress.lesson_id,
        watched_seconds=progress.watched_seconds,
        total_seconds=lesson.video_duration,
        is_completed=progress.is_completed,
        last_position=progress.last_position,
        last_accessed_at=progress.last_accessed_at,
    )
    
    return result


@router.get("/{lesson_id}/progress", response_model=LessonProgressResponse)
async def get_progress(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get lesson progress for current user."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    progress = db.query(LessonProgress).filter(
        LessonProgress.lesson_id == lesson_id,
        LessonProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        # Return default progress
        from datetime import datetime, timezone
        return LessonProgressResponse(
            lesson_id=lesson_id,
            watched_seconds=0,
            total_seconds=lesson.video_duration,
            is_completed=False,
            last_position=0,
            last_accessed_at=datetime.now(timezone.utc),
        )
    
    return LessonProgressResponse(
        lesson_id=progress.lesson_id,
        watched_seconds=progress.watched_seconds,
        total_seconds=lesson.video_duration,
        is_completed=progress.is_completed,
        last_position=progress.last_position,
        last_accessed_at=progress.last_accessed_at,
    )
