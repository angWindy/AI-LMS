"""Slide deck API endpoints."""
import logging
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import CurrentUser, DBSession, InstructorUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.lesson import Lesson
from app.models.slide_deck import SlideDeck
from app.models.user import User, UserRole
from app.schemas.common import Message
from app.schemas.slide_deck import SlideDeckGenerateDraftRequest, SlideDeckResponse
from app.services.slide_generator_service import SlideGeneratorService
from app.utils.file_handler import file_handler

router = APIRouter(prefix="/slides", tags=["Slides"])
logger = logging.getLogger(__name__)


def check_course_owner(db: DBSession, course_id: uuid.UUID, user: User) -> Course:
    """Check if user owns the course or is admin."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return course


def ensure_learner_enrolled(db: DBSession, course_id: uuid.UUID, user: User) -> None:
    """Ensure learner is actively enrolled before accessing slide decks."""
    if user.role != UserRole.LEARNER:
        return

    is_enrolled = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.user_id == user.id,
        Enrollment.status == EnrollmentStatus.ACTIVE,
    ).first() is not None

    if not is_enrolled:
        raise ForbiddenException("You must be enrolled in this course")


def check_slide_deck_access(
    db: DBSession,
    slide_deck_id: uuid.UUID,
    user: User,
    require_owner: bool = False,
) -> SlideDeck:
    """Check slide deck access based on role and ownership."""
    slide_deck = db.query(SlideDeck).options(
        joinedload(SlideDeck.course),
    ).filter(SlideDeck.id == slide_deck_id).first()

    if not slide_deck:
        raise NotFoundException("Slide deck not found")

    is_owner = user.role == UserRole.ADMIN or slide_deck.course.instructor_id == user.id
    if require_owner and not is_owner:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    if not is_owner and not slide_deck.is_published:
        raise NotFoundException("Slide deck not found")

    if user.role == UserRole.LEARNER:
        ensure_learner_enrolled(db, slide_deck.course_id, user)

    return slide_deck


@router.post("/generate-draft", response_model=SlideDeckResponse, status_code=status.HTTP_201_CREATED)
async def generate_slide_deck_draft(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    payload: SlideDeckGenerateDraftRequest,
):
    """Generate an unpublished lecture slide deck draft for one lesson using LLM."""
    check_course_owner(db, course_id, current_user)

    course = db.query(Course).options(
        joinedload(Course.materials),
    ).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    lesson = db.query(Lesson).options(
        joinedload(Lesson.materials),
    ).filter(
        Lesson.id == payload.lesson_id,
        Lesson.course_id == course_id,
    ).first()
    if not lesson:
        raise NotFoundException("Lesson not found in this course")

    generator_service = SlideGeneratorService()
    try:
        generation_result = generator_service.generate_slides(
            course=course,
            lesson=lesson,
            slide_count=payload.slide_count,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "[Error] Unexpected error during slide deck generation course_id=%s lesson_id=%s slide_count=%s error=%s",
            course_id,
            payload.lesson_id,
            payload.slide_count,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tạo slide bài giảng bằng AI thất bại: {exc}",
        ) from exc

    max_order = db.query(func.max(SlideDeck.order_index)).filter(
        SlideDeck.course_id == course_id
    ).scalar()
    next_order = (max_order or 0) + 1

    slide_deck_id = uuid.uuid4()
    title = (payload.title or "").strip() or f"{lesson.title} - Slide bai giang AI"
    pdf_info = generator_service.render_pdf(
        slides_json=generation_result.slides_json,
        lesson_id=lesson.id,
        slide_deck_id=slide_deck_id,
    )
    slide_deck = SlideDeck(
        id=slide_deck_id,
        course_id=course_id,
        lesson_id=lesson.id,
        title=title,
        slide_count=payload.slide_count,
        ir_json=generation_result.ir_json,
        slides_json=generation_result.slides_json,
        pdf_url=pdf_info["pdf_url"],
        pdf_file_size=pdf_info["pdf_file_size"],
        pdf_mime_type=pdf_info["pdf_mime_type"],
        provider=generation_result.provider,
        model=generation_result.model,
        is_published=False,
        order_index=next_order,
    )
    db.add(slide_deck)
    db.commit()
    db.refresh(slide_deck)

    logger.info(
        "[Success] Slide deck draft generated slide_deck_id=%s course_id=%s lesson_id=%s title=%s created_by=%s slide_count=%s provider=%s model=%s",
        slide_deck.id,
        slide_deck.course_id,
        slide_deck.lesson_id,
        slide_deck.title,
        current_user.email,
        slide_deck.slide_count,
        generation_result.provider,
        generation_result.model,
    )

    return slide_deck


@router.get("", response_model=list[SlideDeckResponse])
async def list_slide_decks(
    db: DBSession,
    course_id: uuid.UUID,
    current_user: CurrentUser,
    lesson_id: uuid.UUID | None = None,
    include_unpublished: bool = Query(False),
):
    """List slide decks for a course or lesson."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    ensure_learner_enrolled(db, course_id, current_user)

    query = db.query(SlideDeck).filter(SlideDeck.course_id == course_id)
    if lesson_id:
        query = query.filter(SlideDeck.lesson_id == lesson_id)

    is_owner = current_user.role == UserRole.ADMIN or course.instructor_id == current_user.id
    if current_user.role == UserRole.LEARNER or not include_unpublished or not is_owner:
        query = query.filter(SlideDeck.is_published.is_(True))

    return query.order_by(SlideDeck.order_index).all()


@router.get("/{slide_deck_id}", response_model=SlideDeckResponse)
async def get_slide_deck(
    db: DBSession,
    slide_deck_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get one slide deck."""
    return check_slide_deck_access(db, slide_deck_id, current_user)


@router.post("/{slide_deck_id}/publish", response_model=SlideDeckResponse)
async def publish_slide_deck(
    db: DBSession,
    slide_deck_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Publish a slide deck."""
    slide_deck = check_slide_deck_access(db, slide_deck_id, current_user, require_owner=True)
    slide_deck.is_published = True
    db.commit()
    db.refresh(slide_deck)
    return slide_deck


@router.delete("/{slide_deck_id}", response_model=Message)
async def delete_slide_deck(
    db: DBSession,
    slide_deck_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete a slide deck."""
    slide_deck = check_slide_deck_access(db, slide_deck_id, current_user, require_owner=True)
    slide_deck_title = slide_deck.title
    slide_deck_course_id = slide_deck.course_id
    slide_deck_pdf_url = slide_deck.pdf_url

    db.delete(slide_deck)
    db.commit()

    if slide_deck_pdf_url:
        file_handler.delete_file(slide_deck_pdf_url)

    logger.info(
        "[Success] Slide deck deleted slide_deck_id=%s course_id=%s title=%s deleted_by=%s",
        slide_deck_id,
        slide_deck_course_id,
        slide_deck_title,
        current_user.email,
    )

    return Message(message="Slide deck deleted successfully")
