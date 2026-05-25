"""
Lesson management API endpoints.
"""
import logging
from pathlib import Path
from typing import List, Optional
import uuid

from fastapi import APIRouter, status, UploadFile, File, Form
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import DBSession, CurrentUser, InstructorUser
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.material import Material
from app.models.lesson_progress import LessonProgress
from app.schemas.lesson import (
    LessonCreate,
    LessonUpdate,
    LessonOrderUpdate,
    LessonResponse,
    LessonDetailResponse,
    LessonProgressUpdate,
    LessonProgressResponse,
    MaterialResponse,
)
from app.schemas.common import Message
from app.utils.file_handler import file_handler
from app.services.rag_ingestion import index_material, remove_lesson_index, remove_material_index

router = APIRouter(prefix="/lessons", tags=["Lessons"])
logger = logging.getLogger(__name__)


def _material_title_or_default(
    title: Optional[str],
    file: Optional[UploadFile],
    external_url: Optional[str],
) -> str:
    normalized_title = (title or "").strip()
    if normalized_title:
        return normalized_title
    if file and file.filename:
        return Path(file.filename).stem.strip() or file.filename
    if external_url:
        return Path(external_url.rstrip("/")).stem or external_url
    return "Tài liệu"


def check_course_access(db: DBSession, course_id: uuid.UUID, user: User, require_owner: bool = False):
    # Kiểm tra quyền truy cập khóa học.
    """Check if user has access to the course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")
    
    if require_owner:
        if user.role != UserRole.ADMIN and course.instructor_id != user.id:
            raise ForbiddenException("Only course instructor or admin can perform this action")
    
    return course


def check_lesson_access(db: DBSession, lesson_id: uuid.UUID, user: User, require_owner: bool = False):
    # Kiểm tra quyền truy cập buổi học.
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
    # Tạo buổi học mới trong khóa học.
    """Create a new lesson in a course."""
    # Check course access
    check_course_access(db, course_id, current_user, require_owner=True)
    
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
        video_url=lesson_data.video_url,
        video_duration=lesson_data.video_duration,
    )
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    logger.info(
        "[Success] Lesson created lesson_id=%s course_id=%s title=%s created_by=%s",
        lesson.id,
        lesson.course_id,
        lesson.title,
        current_user.email,
    )
    
    return lesson


@router.get("/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: CurrentUser,
):
    # Lấy chi tiết buổi học (kèm material).
    """Get lesson details with materials."""
    lesson = db.query(Lesson).options(
        joinedload(Lesson.materials),
        joinedload(Lesson.course)
    ).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    is_admin = current_user.role == UserRole.ADMIN
    is_instructor = lesson.course.instructor_id == current_user.id
    if not (is_admin or is_instructor or lesson.is_preview or lesson.is_published):
        raise ForbiddenException("This lesson is not available")
    
    return lesson


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    lesson_data: LessonUpdate,
    current_user: InstructorUser,
):
    # Cập nhật nội dung buổi học.
    """Update a lesson."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    # Update fields
    update_data = lesson_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)
    
    db.commit()
    db.refresh(lesson)

    logger.info(
        "[Success] Lesson updated lesson_id=%s course_id=%s title=%s updated_by=%s is_published=%s",
        lesson.id,
        lesson.course_id,
        lesson.title,
        current_user.email,
        lesson.is_published,
    )
    
    return lesson


@router.delete("/{lesson_id}", response_model=Message)
async def delete_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
):
    # Xóa buổi học và tài liệu kèm theo.
    """Delete a lesson and its materials."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)

    lesson_title = lesson.title
    course_id = lesson.course_id

    # Best-effort RAG cleanup before the lesson/material rows are removed.
    try:
        remove_lesson_index(db, lesson.id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "[RAG] Cleanup failed for lesson_id=%s error=%s",
            lesson.id, exc,
        )
    
    # Delete associated materials' files
    for material in lesson.materials:
        if material.file_url:
            file_handler.delete_file(material.file_url)
    
    # Delete lesson (cascades to materials)
    db.delete(lesson)
    db.commit()

    logger.info(
        "[Success] Lesson deleted lesson_id=%s course_id=%s title=%s deleted_by=%s",
        lesson_id,
        course_id,
        lesson_title,
        current_user.email,
    )
    
    return Message(message="Lesson deleted successfully")


@router.patch("/{lesson_id}/order", response_model=LessonResponse)
async def update_lesson_order(
    db: DBSession,
    lesson_id: uuid.UUID,
    order_data: LessonOrderUpdate,
    current_user: InstructorUser,
):
    # Cập nhật thứ tự hiển thị buổi học.
    """Update lesson order within a course."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    lesson.order_index = order_data.order_index
    db.commit()
    db.refresh(lesson)

    logger.info(
        "[Success] Lesson order updated lesson_id=%s course_id=%s order_index=%s updated_by=%s",
        lesson.id,
        lesson.course_id,
        lesson.order_index,
        current_user.email,
    )
    
    return lesson


@router.post("/{lesson_id}/publish", response_model=LessonResponse)
async def publish_lesson(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
):
    # Xuất bản buổi học.
    """Publish a lesson."""
    lesson = check_lesson_access(db, lesson_id, current_user, require_owner=True)
    
    lesson.is_published = True
    db.commit()
    db.refresh(lesson)

    logger.info(
        "[Success] Lesson published lesson_id=%s course_id=%s title=%s published_by=%s",
        lesson.id,
        lesson.course_id,
        lesson.title,
        current_user.email,
    )
    
    return lesson


# ============ MATERIALS ============

@router.post("/{lesson_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: InstructorUser,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    material_type: str = Form(..., alias="type"),
    file: Optional[UploadFile] = File(None),
    external_url: Optional[str] = Form(None),
):
    # Tạo tài liệu cho buổi học (có thể upload).
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
        course_id=lesson.course_id,
        lesson_id=lesson_id,
        title=_material_title_or_default(title, file, external_url),
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

    logger.info(
        "[Success] Lesson material created material_id=%s lesson_id=%s course_id=%s type=%s title=%s created_by=%s file_size=%s",
        material.id,
        material.lesson_id,
        material.course_id,
        material.type,
        material.title,
        current_user.email,
        material.file_size,
    )

    # Best-effort RAG ingestion. Never block the upload on indexing failure.
    try:
        index_material(db, material)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "[RAG] Ingestion failed for material_id=%s error=%s",
            material.id, exc,
        )

    return material


@router.get("/{lesson_id}/materials", response_model=List[MaterialResponse])
async def list_materials(
    db: DBSession,
    lesson_id: uuid.UUID,
    current_user: CurrentUser,
):
    # Danh sách tài liệu của buổi học.
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
    # Xóa tài liệu buổi học.
    """Delete a material."""
    material = db.query(Material).options(
        joinedload(Material.lesson).joinedload(Lesson.course)
    ).filter(Material.id == material_id).first()
    
    if not material:
        raise NotFoundException("Material not found")
    
    # Check ownership
    if current_user.role != UserRole.ADMIN and material.lesson.course.instructor_id != current_user.id:
        raise ForbiddenException("Only course instructor or admin can delete this material")

    material_lesson_id = material.lesson_id
    material_course_id = material.course_id
    material_title = material.title

    # Best-effort RAG cleanup before we drop the row.
    try:
        remove_material_index(db, material.id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "[RAG] Cleanup failed for material_id=%s error=%s",
            material.id, exc,
        )

    # Delete file if exists
    if material.file_url:
        file_handler.delete_file(material.file_url)

    db.delete(material)
    db.commit()

    logger.info(
        "[Success] Lesson material deleted material_id=%s lesson_id=%s course_id=%s title=%s deleted_by=%s",
        material_id,
        material_lesson_id,
        material_course_id,
        material_title,
        current_user.email,
    )

    return Message(message="Material deleted successfully")


# ============ LESSON PROGRESS ============

@router.post("/{lesson_id}/progress", response_model=LessonProgressResponse)
async def update_progress(
    db: DBSession,
    lesson_id: uuid.UUID,
    progress_data: LessonProgressUpdate,
    current_user: CurrentUser,
):
    # Lưu tiến độ học của học viên.
    """Update or create lesson progress for current user."""
    # Verify lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise NotFoundException("Lesson not found")
    
    # Get or create progress
    progress = db.query(LessonProgress).filter(
        LessonProgress.lesson_id == lesson_id,
        LessonProgress.user_id == current_user.id
    ).first()
    created_new = progress is None
    
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

    logger.info(
        "[Success] Lesson progress updated lesson_id=%s course_id=%s user=%s progress_mode=%s watched_seconds=%s last_position=%s completed=%s",
        lesson_id,
        lesson.course_id,
        current_user.email,
        "created" if created_new else "updated",
        progress.watched_seconds,
        progress.last_position,
        progress.is_completed,
    )
    
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
    # Lấy tiến độ học của học viên.
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
