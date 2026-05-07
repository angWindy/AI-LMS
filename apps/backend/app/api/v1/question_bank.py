"""
Question bank API endpoints.
"""
import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import DBSession, InstructorUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question_bank import QuestionBankOption, QuestionBankQuestion
from app.models.user import User, UserRole
from app.schemas.common import Message
from app.schemas.question_bank import (
    QuestionBankCourseResponse,
    QuestionBankGenerateRequest,
    QuestionBankOptionCreate,
    QuestionBankQuestionCreate,
    QuestionBankQuestionResponse,
    QuestionBankQuestionUpdate,
)
from app.services.assignment_generator_service import AssignmentGeneratorService

router = APIRouter(prefix="/question-bank", tags=["Question Bank"])
logger = logging.getLogger(__name__)


def ensure_course_access(db: DBSession, course_id: uuid.UUID, user: User) -> Course:
    """Return a course if the current admin/instructor can manage its question bank."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can manage this question bank")

    return course


def ensure_lesson_in_course(db: DBSession, course_id: uuid.UUID, lesson_id: uuid.UUID | None) -> Lesson | None:
    """Validate optional lesson scope."""
    if lesson_id is None:
        return None

    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.course_id == course_id,
    ).first()
    if not lesson:
        raise NotFoundException("Lesson not found in this course")
    return lesson


def get_question_for_update(db: DBSession, question_id: uuid.UUID, user: User) -> QuestionBankQuestion:
    """Load a question and enforce manager access."""
    question = db.query(QuestionBankQuestion).options(
        joinedload(QuestionBankQuestion.course),
        joinedload(QuestionBankQuestion.lesson),
        joinedload(QuestionBankQuestion.options),
    ).filter(QuestionBankQuestion.id == question_id).first()

    if not question:
        raise NotFoundException("Question not found")

    if user.role != UserRole.ADMIN and question.course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can manage this question")

    return question


def add_options_to_question(
    db: DBSession,
    question: QuestionBankQuestion,
    options_data: List[QuestionBankOptionCreate],
) -> None:
    """Attach full option set to a question bank question."""
    for option_index, option_data in enumerate(options_data):
        option = QuestionBankOption(
            question_id=question.id,
            option_text=option_data.option_text,
            is_correct=option_data.is_correct,
            order_index=option_index,
        )
        db.add(option)


def serialize_question(question: QuestionBankQuestion) -> QuestionBankQuestionResponse:
    """Build response with denormalized course and lesson titles for the UI."""
    return QuestionBankQuestionResponse(
        id=question.id,
        course_id=question.course_id,
        lesson_id=question.lesson_id,
        question_text=question.question_text,
        explanation=question.explanation,
        difficulty=question.difficulty,
        purpose_type=question.purpose_type,
        order_index=question.order_index,
        course_title=question.course.title,
        lesson_title=question.lesson.title if question.lesson else None,
        options=question.options,
        created_at=question.created_at,
        updated_at=question.updated_at,
    )


@router.get("/courses", response_model=List[QuestionBankCourseResponse])
async def list_question_bank_courses(
    db: DBSession,
    current_user: InstructorUser,
):
    """List courses visible in the question bank."""
    query = db.query(Course)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Course.instructor_id == current_user.id)

    courses = query.order_by(Course.title.asc()).all()
    return [
        QuestionBankCourseResponse(
            id=course.id,
            title=course.title,
            slug=course.slug,
            instructor_id=course.instructor_id,
        )
        for course in courses
    ]


@router.get("/questions", response_model=List[QuestionBankQuestionResponse])
async def list_questions(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID | None = Query(None),
    lesson_id: uuid.UUID | None = Query(None),
):
    """List reusable questions for accessible courses, optionally filtered by course and lesson."""
    query = db.query(QuestionBankQuestion).options(
        joinedload(QuestionBankQuestion.course),
        joinedload(QuestionBankQuestion.lesson),
        joinedload(QuestionBankQuestion.options),
    ).join(QuestionBankQuestion.course)

    if course_id is not None:
        ensure_course_access(db, course_id, current_user)
        query = query.filter(QuestionBankQuestion.course_id == course_id)
    elif current_user.role != UserRole.ADMIN:
        query = query.filter(Course.instructor_id == current_user.id)

    if lesson_id is not None:
        if course_id is None:
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if not lesson:
                raise NotFoundException("Lesson not found")
            ensure_course_access(db, lesson.course_id, current_user)
            query = query.filter(QuestionBankQuestion.course_id == lesson.course_id)
        else:
            ensure_lesson_in_course(db, course_id, lesson_id)
        query = query.filter(QuestionBankQuestion.lesson_id == lesson_id)

    questions = query.order_by(
        Course.title.asc(),
        QuestionBankQuestion.order_index.asc(),
        QuestionBankQuestion.created_at.desc(),
    ).all()
    return [serialize_question(question) for question in questions]


@router.post("/questions", response_model=QuestionBankQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    db: DBSession,
    current_user: InstructorUser,
    payload: QuestionBankQuestionCreate,
):
    """Create one reusable question manually."""
    course = ensure_course_access(db, payload.course_id, current_user)
    ensure_lesson_in_course(db, course.id, payload.lesson_id)

    max_order = db.query(func.max(QuestionBankQuestion.order_index)).filter(
        QuestionBankQuestion.course_id == course.id
    ).scalar()
    next_order = (max_order or 0) + 1

    question = QuestionBankQuestion(
        course_id=course.id,
        lesson_id=payload.lesson_id,
        question_text=payload.question_text,
        explanation=payload.explanation,
        difficulty=payload.difficulty,
        purpose_type=payload.purpose_type,
        order_index=next_order,
    )
    db.add(question)
    db.flush()
    add_options_to_question(db, question, payload.options)

    db.commit()
    db.refresh(question)

    logger.info(
        "[Success] Question bank question created question_id=%s course_id=%s lesson_id=%s created_by=%s",
        question.id,
        question.course_id,
        question.lesson_id,
        current_user.email,
    )

    return serialize_question(question)


@router.post("/generate", response_model=List[QuestionBankQuestionResponse], status_code=status.HTTP_201_CREATED)
async def generate_questions(
    db: DBSession,
    current_user: InstructorUser,
    payload: QuestionBankGenerateRequest,
):
    """Generate reusable question bank questions for one lesson using the existing LLM workflow."""
    course = db.query(Course).options(
        joinedload(Course.materials),
    ).filter(Course.id == payload.course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    ensure_course_access(db, course.id, current_user)

    lesson = db.query(Lesson).options(
        joinedload(Lesson.materials),
    ).filter(
        Lesson.id == payload.lesson_id,
        Lesson.course_id == course.id,
    ).first()
    if not lesson:
        raise NotFoundException("Lesson not found in this course")

    generator_service = AssignmentGeneratorService()
    try:
        generation_result = generator_service.generate_questions(
            course=course,
            lesson=lesson,
            question_count=payload.question_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "[Error] Unexpected error during question bank generation course_id=%s lesson_id=%s question_count=%s error=%s",
            course.id,
            lesson.id,
            payload.question_count,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tạo câu hỏi bằng AI thất bại: {exc}",
        ) from exc

    max_order = db.query(func.max(QuestionBankQuestion.order_index)).filter(
        QuestionBankQuestion.course_id == course.id
    ).scalar()
    next_order = (max_order or 0) + 1

    created_questions: list[QuestionBankQuestion] = []
    for offset, generated_question in enumerate(generation_result.questions):
        question = QuestionBankQuestion(
            course_id=course.id,
            lesson_id=lesson.id,
            question_text=generated_question.question_text,
            explanation=generated_question.explanation,
            difficulty=payload.difficulty,
            purpose_type=payload.purpose_type,
            order_index=next_order + offset,
        )
        db.add(question)
        db.flush()
        add_options_to_question(db, question, generated_question.options)
        created_questions.append(question)

    db.commit()
    for question in created_questions:
        db.refresh(question)

    logger.info(
        "[Success] Question bank generated course_id=%s lesson_id=%s created_by=%s question_count=%s provider=%s model=%s",
        course.id,
        lesson.id,
        current_user.email,
        len(created_questions),
        generation_result.provider,
        generation_result.model,
    )

    return [serialize_question(question) for question in created_questions]


@router.put("/questions/{question_id}", response_model=QuestionBankQuestionResponse)
async def update_question(
    db: DBSession,
    current_user: InstructorUser,
    question_id: uuid.UUID,
    payload: QuestionBankQuestionUpdate,
):
    """Update a reusable question and optionally replace its options."""
    question = get_question_for_update(db, question_id, current_user)
    ensure_lesson_in_course(db, question.course_id, payload.lesson_id)

    question.lesson_id = payload.lesson_id
    question.question_text = payload.question_text
    question.explanation = payload.explanation
    question.difficulty = payload.difficulty
    question.purpose_type = payload.purpose_type

    if payload.options is not None:
        db.query(QuestionBankOption).filter(
            QuestionBankOption.question_id == question.id
        ).delete(synchronize_session=False)
        add_options_to_question(db, question, payload.options)

    db.commit()
    db.refresh(question)

    logger.info(
        "[Success] Question bank question updated question_id=%s course_id=%s updated_by=%s purpose_type=%s",
        question.id,
        question.course_id,
        current_user.email,
        question.purpose_type,
    )

    return serialize_question(question)


@router.delete("/questions/{question_id}", response_model=Message)
async def delete_question(
    db: DBSession,
    current_user: InstructorUser,
    question_id: uuid.UUID,
):
    """Delete one reusable question from the question bank."""
    question = get_question_for_update(db, question_id, current_user)
    course_id = question.course_id

    db.delete(question)
    db.commit()

    logger.info(
        "[Success] Question bank question deleted question_id=%s course_id=%s deleted_by=%s",
        question_id,
        course_id,
        current_user.email,
    )

    return Message(message="Question deleted successfully")
