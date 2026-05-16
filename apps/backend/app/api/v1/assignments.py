"""
Assignment API endpoints.
"""
import logging
import random
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from llm.prompts.assignment_generator import difficulty_distribution
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import CurrentUser, DBSession, InstructorUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.assignment import (
    Assignment,
    AssignmentOption,
    AssignmentQuestion,
    QuestionDifficulty,
    QuestionPurposeType,
)
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question_bank import QuestionBankQuestion
from app.models.user import User, UserRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentGenerateDraftRequest,
    AssignmentGenerateFromBankRequest,
    AssignmentOptionCreate,
    AssignmentQuestionCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.common import Message
from app.services.assignment_generator_service import AssignmentGeneratorService

router = APIRouter(prefix="/assignments", tags=["Assignments"])
logger = logging.getLogger(__name__)


def check_course_owner(db: DBSession, course_id: uuid.UUID, user: User) -> Course:
    """Check if user owns the course or is admin."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return course


def check_assignment_access(db: DBSession, assignment_id: uuid.UUID, user: User, require_owner: bool = False) -> Assignment:
    """Check assignment access based on role and ownership."""
    assignment = db.query(Assignment).options(
        joinedload(Assignment.course),
        joinedload(Assignment.questions).joinedload(AssignmentQuestion.options),
    ).filter(Assignment.id == assignment_id).first()

    if not assignment:
        raise NotFoundException("Assignment not found")

    if require_owner and user.role != UserRole.ADMIN and assignment.course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return assignment


def add_questions_to_assignment(db: DBSession, assignment: Assignment, questions_data: list[AssignmentQuestionCreate]):
    """Attach full question tree to assignment."""
    for question_index, question_data in enumerate(questions_data):
        question = AssignmentQuestion(
            assignment_id=assignment.id,
            question_text=question_data.question_text,
            difficulty=question_data.difficulty,
            purpose_type=question_data.purpose_type,
            order_index=question_index,
        )
        db.add(question)
        db.flush()

        for option_index, option_data in enumerate(question_data.options):
            option = AssignmentOption(
                question_id=question.id,
                option_text=option_data.option_text,
                is_correct=option_data.is_correct,
                order_index=option_index,
            )
            db.add(option)


def build_assignment_question_from_bank(question: QuestionBankQuestion) -> AssignmentQuestionCreate:
    """Clone one reusable question bank item into an assignment payload."""
    return AssignmentQuestionCreate(
        question_text=question.question_text,
        difficulty=question.difficulty,
        purpose_type=question.purpose_type,
        options=[
            AssignmentOptionCreate(
                option_text=option.option_text,
                is_correct=option.is_correct,
            )
            for option in sorted(question.options, key=lambda option: option.order_index)
        ],
    )


def select_review_questions_from_bank(
    db: DBSession,
    course_id: uuid.UUID,
    question_count: int,
) -> list[QuestionBankQuestion]:
    """Randomly select practice/shared bank questions with a 40/40/20 difficulty distribution."""
    expected_counts = difficulty_distribution(question_count)
    selected_questions: list[QuestionBankQuestion] = []
    shortages: list[str] = []

    for difficulty_value, expected_count in expected_counts.items():
        if expected_count == 0:
            continue

        candidates = (
            db.query(QuestionBankQuestion)
            .options(joinedload(QuestionBankQuestion.options))
            .filter(
                QuestionBankQuestion.course_id == course_id,
                QuestionBankQuestion.difficulty == QuestionDifficulty(difficulty_value),
                QuestionBankQuestion.purpose_type.in_([
                    QuestionPurposeType.PRACTICE,
                    QuestionPurposeType.SHARED,
                ]),
            )
            .all()
        )

        if len(candidates) < expected_count:
            shortages.append(f"{difficulty_value}: cần {expected_count}, hiện có {len(candidates)}")
            continue

        selected_questions.extend(random.sample(candidates, expected_count))

    if shortages:
        raise ValueError(
            "Ngân hàng câu hỏi chưa đủ câu Luyện tập/Dùng chung theo tỉ lệ 40/40/20: "
            + "; ".join(shortages)
        )

    random.shuffle(selected_questions)
    return selected_questions


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    assignment_data: AssignmentCreate,
):
    """Create a new assignment for a course."""
    check_course_owner(db, course_id, current_user)

    if assignment_data.lesson_id:
        lesson = db.query(Lesson).filter(
            Lesson.id == assignment_data.lesson_id,
            Lesson.course_id == course_id,
        ).first()
        if not lesson:
            raise NotFoundException("Lesson not found in this course")

    max_order = db.query(func.max(Assignment.order_index)).filter(
        Assignment.course_id == course_id
    ).scalar()
    next_order = (max_order or 0) + 1

    assignment = Assignment(
        course_id=course_id,
        lesson_id=assignment_data.lesson_id,
        title=assignment_data.title,
        is_published=False,
        order_index=next_order,
    )

    db.add(assignment)
    db.flush()

    add_questions_to_assignment(db, assignment, assignment_data.questions)

    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Assignment created assignment_id=%s course_id=%s lesson_id=%s title=%s created_by=%s question_count=%s",
        assignment.id,
        assignment.course_id,
        assignment.lesson_id,
        assignment.title,
        current_user.email,
        len(assignment_data.questions),
    )

    return assignment


@router.post("/generate-draft", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def generate_assignment_draft(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    payload: AssignmentGenerateDraftRequest,
):
    """Generate an unpublished assignment draft for one lesson using LLM."""
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

    generator_service = AssignmentGeneratorService()
    try:
        generation_result = generator_service.generate_questions(
            course=course,
            lesson=lesson,
            question_count=payload.question_count,
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
            "[Error] Unexpected error during assignment draft generation course_id=%s lesson_id=%s question_count=%s error=%s",
            course_id,
            payload.lesson_id,
            payload.question_count,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tạo assignment bằng AI thất bại: {exc}",
        ) from exc

    max_order = db.query(func.max(Assignment.order_index)).filter(
        Assignment.course_id == course_id
    ).scalar()
    next_order = (max_order or 0) + 1

    assignment_title = (payload.title or "").strip() or f"{lesson.title} - Bai tap AI"
    assignment = Assignment(
        course_id=course_id,
        lesson_id=lesson.id,
        title=assignment_title,
        is_published=False,
        order_index=next_order,
    )
    db.add(assignment)
    db.flush()

    add_questions_to_assignment(db, assignment, generation_result.questions)

    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Assignment draft generated assignment_id=%s course_id=%s lesson_id=%s title=%s created_by=%s question_count=%s provider=%s model=%s",
        assignment.id,
        assignment.course_id,
        assignment.lesson_id,
        assignment.title,
        current_user.email,
        len(generation_result.questions),
        generation_result.provider,
        generation_result.model,
    )

    return assignment


@router.post("/generate-from-bank", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def generate_assignment_from_question_bank(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    payload: AssignmentGenerateFromBankRequest,
):
    """Generate an unpublished review assignment from random practice/shared question bank items."""
    check_course_owner(db, course_id, current_user)

    lesson = None
    if payload.lesson_id:
        lesson = db.query(Lesson).filter(
            Lesson.id == payload.lesson_id,
            Lesson.course_id == course_id,
        ).first()
        if not lesson:
            raise NotFoundException("Lesson not found in this course")

    try:
        selected_questions = select_review_questions_from_bank(
            db=db,
            course_id=course_id,
            question_count=payload.question_count,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    max_order = db.query(func.max(Assignment.order_index)).filter(
        Assignment.course_id == course_id
    ).scalar()
    next_order = (max_order or 0) + 1

    title_prefix = lesson.title if lesson else "Bài tập ôn tập"
    assignment_title = (payload.title or "").strip() or f"{title_prefix} - Bài tập ôn tập"
    assignment = Assignment(
        course_id=course_id,
        lesson_id=payload.lesson_id,
        title=assignment_title,
        is_published=False,
        order_index=next_order,
    )
    db.add(assignment)
    db.flush()

    assignment_questions = [build_assignment_question_from_bank(question) for question in selected_questions]
    add_questions_to_assignment(db, assignment, assignment_questions)

    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Assignment draft generated from question bank assignment_id=%s course_id=%s lesson_id=%s title=%s created_by=%s question_count=%s",
        assignment.id,
        assignment.course_id,
        assignment.lesson_id,
        assignment.title,
        current_user.email,
        len(assignment_questions),
    )

    return assignment


@router.get("", response_model=list[AssignmentResponse])
async def list_assignments(
    db: DBSession,
    course_id: uuid.UUID,
    current_user: CurrentUser,
    include_unpublished: bool = Query(False),
):
    """List assignments for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    query = db.query(Assignment).options(
        joinedload(Assignment.questions).joinedload(AssignmentQuestion.options),
    ).filter(Assignment.course_id == course_id)

    if current_user.role == UserRole.LEARNER or not include_unpublished:
        query = query.filter(Assignment.is_published.is_(True))

    return query.order_by(Assignment.order_index).all()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get assignment details."""
    assignment = check_assignment_access(db, assignment_id, current_user)

    if current_user.role == UserRole.LEARNER:
        if not assignment.is_published:
            raise NotFoundException("Assignment not found")
        return assignment

    if not assignment.is_published:
        is_owner = current_user.role == UserRole.ADMIN or assignment.course.instructor_id == current_user.id
        if not is_owner:
            raise NotFoundException("Assignment not found")

    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    assignment_data: AssignmentUpdate,
    current_user: InstructorUser,
):
    """Update assignment title, publish flag, and question set."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)

    if assignment_data.title is not None:
        assignment.title = assignment_data.title

    if assignment_data.is_published is not None:
        assignment.is_published = assignment_data.is_published

    if assignment_data.questions is not None:
        db.query(AssignmentOption).filter(
            AssignmentOption.question_id.in_(
                db.query(AssignmentQuestion.id).filter(AssignmentQuestion.assignment_id == assignment_id)
            )
        ).delete(synchronize_session=False)
        db.query(AssignmentQuestion).filter(
            AssignmentQuestion.assignment_id == assignment_id
        ).delete(synchronize_session=False)

        add_questions_to_assignment(db, assignment, assignment_data.questions)

    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Assignment updated assignment_id=%s course_id=%s title=%s updated_by=%s is_published=%s question_count=%s",
        assignment.id,
        assignment.course_id,
        assignment.title,
        current_user.email,
        assignment.is_published,
        len(assignment.questions),
    )

    return assignment


@router.delete("/{assignment_id}", response_model=Message)
async def delete_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete an assignment."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)

    assignment_course_id = assignment.course_id
    assignment_title = assignment.title

    db.delete(assignment)
    db.commit()

    logger.info(
        "[Success] Assignment deleted assignment_id=%s course_id=%s title=%s deleted_by=%s",
        assignment_id,
        assignment_course_id,
        assignment_title,
        current_user.email,
    )

    return Message(message="Assignment deleted successfully")


@router.post("/{assignment_id}/publish", response_model=AssignmentResponse)
async def publish_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Publish an assignment."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)

    assignment.is_published = True
    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Assignment published assignment_id=%s course_id=%s title=%s published_by=%s",
        assignment.id,
        assignment.course_id,
        assignment.title,
        current_user.email,
    )

    return assignment
