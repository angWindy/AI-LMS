"""
Assignment API endpoints.
"""
import logging
import random
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from llm.prompts.assignment_generator import difficulty_distribution
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import CurrentUser, DBSession, InstructorUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.assignment import (
    Assignment,
    AssignmentLessonScope,
    AssignmentOption,
    AssignmentQuestion,
    AssignmentQuestionType,
    AssignmentType,
    QuestionDifficulty,
    QuestionPurposeType,
)
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question_bank import QuestionBankQuestion
from app.models.submission import Submission, SubmissionAnswer, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentGenerateDraftRequest,
    AssignmentGenerateFromBankRequest,
    AssignmentGenerateTestRequest,
    AssignmentOptionCreate,
    AssignmentQuestionCreate,
    AssignmentResponse,
    AssignmentSubmitRequest,
    AssignmentUpdate,
    SubmissionResponse,
)
from app.schemas.common import Message
from app.services.assignment_feedback_service import AssignmentFeedbackService
from app.services.assignment_generator_service import AssignmentGeneratorService

router = APIRouter(prefix="/assignments", tags=["Assignments"])
logger = logging.getLogger(__name__)

TEST_ESSAY_RATIOS = {
    QuestionDifficulty.MEDIUM: 0.5,
    QuestionDifficulty.HARD: 0.7,
}


def check_course_owner(db: DBSession, course_id: uuid.UUID, user: User) -> Course:
    # Kiểm tra quyền sở hữu khóa học.
    """Check if user owns the course or is admin."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    if user.role != UserRole.ADMIN and course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return course


def check_assignment_access(db: DBSession, assignment_id: uuid.UUID, user: User, require_owner: bool = False) -> Assignment:
    # Kiểm tra quyền truy cập bài tập.
    """Check assignment access based on role and ownership."""
    assignment = db.query(Assignment).options(
        joinedload(Assignment.course),
        joinedload(Assignment.lesson),
        joinedload(Assignment.lesson_scopes).joinedload(AssignmentLessonScope.lesson),
        joinedload(Assignment.questions).joinedload(AssignmentQuestion.options),
    ).filter(Assignment.id == assignment_id).first()

    if not assignment:
        raise NotFoundException("Assignment not found")

    if require_owner and user.role != UserRole.ADMIN and assignment.course.instructor_id != user.id:
        raise ForbiddenException("Only course instructor or admin can perform this action")

    return assignment


def add_questions_to_assignment(db: DBSession, assignment: Assignment, questions_data: list[AssignmentQuestionCreate]):
    # Thêm cây câu hỏi/đáp án vào assignment.
    """Attach full question tree to assignment."""
    for question_index, question_data in enumerate(questions_data):
        question = AssignmentQuestion(
            assignment_id=assignment.id,
            question_text=question_data.question_text,
            question_type=question_data.question_type,
            correct_answer_text=question_data.correct_answer_text,
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

        if question.correct_answer_text is None:
            correct_option = next((option for option in question_data.options if option.is_correct), None)
            if correct_option:
                question.correct_answer_text = correct_option.option_text


def build_assignment_question_from_bank(
    question: QuestionBankQuestion,
    question_type: AssignmentQuestionType = AssignmentQuestionType.MULTIPLE_CHOICE,
) -> AssignmentQuestionCreate:
    # Chuyển câu hỏi từ ngân hàng sang payload assignment.
    """Clone one reusable question bank item into an assignment payload."""
    sorted_options = sorted(question.options, key=lambda option: option.order_index)
    correct_option = next((option for option in sorted_options if option.is_correct), None)

    if question_type == AssignmentQuestionType.ESSAY:
        return AssignmentQuestionCreate(
            question_text=question.question_text,
            question_type=AssignmentQuestionType.ESSAY,
            correct_answer_text=correct_option.option_text if correct_option else "",
            difficulty=question.difficulty,
            purpose_type=question.purpose_type,
            options=[],
        )

    return AssignmentQuestionCreate(
        question_text=question.question_text,
        question_type=AssignmentQuestionType.MULTIPLE_CHOICE,
        correct_answer_text=correct_option.option_text if correct_option else None,
        difficulty=question.difficulty,
        purpose_type=question.purpose_type,
        options=[
            AssignmentOptionCreate(
                option_text=option.option_text,
                is_correct=option.is_correct,
            )
            for option in sorted_options
        ],
    )


def choose_test_question_types(
    questions: list[QuestionBankQuestion],
) -> dict[uuid.UUID, AssignmentQuestionType]:
    # Chọn một phần câu hỏi dạng tự luận cho bài kiểm tra.
    """Choose essay mode for a portion of medium/hard test questions."""
    selected_types = {
        question.id: AssignmentQuestionType.MULTIPLE_CHOICE
        for question in questions
    }
    for difficulty, ratio in TEST_ESSAY_RATIOS.items():
        group = [question for question in questions if question.difficulty == difficulty]
        if not group:
            continue
        essay_count = max(1, round(len(group) * ratio))
        for question in random.sample(group, min(essay_count, len(group))):
            selected_types[question.id] = AssignmentQuestionType.ESSAY
    return selected_types


def select_review_questions_from_bank(
    db: DBSession,
    course_id: uuid.UUID,
    question_count: int,
) -> list[QuestionBankQuestion]:
    # Chọn ngẫu nhiên câu hỏi luyện tập từ ngân hàng theo tỉ lệ độ khó.
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


def select_test_questions_from_bank(
    db: DBSession,
    course_id: uuid.UUID,
    question_count: int,
    lesson_ids: list[uuid.UUID],
) -> list[QuestionBankQuestion]:
    # Chọn câu hỏi kiểm tra theo phạm vi buổi học và tỉ lệ độ khó.
    """Select assessment-ready test questions with balanced lesson coverage and 40/40/20 difficulty."""
    expected_counts = difficulty_distribution(question_count)
    selected_questions: list[QuestionBankQuestion] = []
    shortages: list[str] = []
    selected_ids: set[uuid.UUID] = set()

    for difficulty_value, expected_count in expected_counts.items():
        if expected_count == 0:
            continue

        query = (
            db.query(QuestionBankQuestion)
            .options(joinedload(QuestionBankQuestion.options))
            .filter(
                QuestionBankQuestion.course_id == course_id,
                QuestionBankQuestion.difficulty == QuestionDifficulty(difficulty_value),
                QuestionBankQuestion.purpose_type.in_([
                    QuestionPurposeType.ASSESSMENT,
                    QuestionPurposeType.SHARED,
                ]),
            )
        )
        if lesson_ids:
            query = query.filter(QuestionBankQuestion.lesson_id.in_(lesson_ids))

        candidates = query.all()
        if len(candidates) < expected_count:
            shortages.append(f"{difficulty_value}: cần {expected_count}, hiện có {len(candidates)}")
            continue

        by_lesson: dict[uuid.UUID | None, list[QuestionBankQuestion]] = {}
        for candidate in candidates:
            by_lesson.setdefault(candidate.lesson_id, []).append(candidate)
        for bucket in by_lesson.values():
            random.shuffle(bucket)

        lesson_order = lesson_ids[:] or list(by_lesson.keys())
        random.shuffle(lesson_order)
        picked_for_difficulty: list[QuestionBankQuestion] = []
        cursor = 0
        while len(picked_for_difficulty) < expected_count:
            lesson_id = lesson_order[cursor % len(lesson_order)] if lesson_order else None
            cursor += 1
            bucket = by_lesson.get(lesson_id) or []
            while bucket and bucket[-1].id in selected_ids:
                bucket.pop()
            if bucket:
                picked = bucket.pop()
                selected_ids.add(picked.id)
                picked_for_difficulty.append(picked)
                continue

            fallback = next(
                (candidate for candidate in candidates if candidate.id not in selected_ids),
                None,
            )
            if fallback is None:
                break
            selected_ids.add(fallback.id)
            picked_for_difficulty.append(fallback)

        if len(picked_for_difficulty) < expected_count:
            shortages.append(f"{difficulty_value}: không đủ câu không trùng lặp")
            continue

        selected_questions.extend(picked_for_difficulty)

    if shortages:
        raise ValueError(
            "Ngân hàng câu hỏi chưa đủ câu Kiểm tra/Dùng chung theo tỉ lệ 40/40/20 trong phạm vi đã chọn: "
            + "; ".join(shortages)
        )

    random.shuffle(selected_questions)
    return selected_questions


def serialize_assignment_for_response(
    assignment: Assignment,
    include_answer_key: bool,
) -> dict:
    # Chuẩn hóa dữ liệu assignment để trả về UI (ẩn đáp án nếu cần).
    """Serialize assignment while optionally hiding answer keys from learners."""
    return {
        "id": assignment.id,
        "course_id": assignment.course_id,
        "lesson_id": assignment.lesson_id,
        "title": assignment.title,
        "assignment_type": assignment.assignment_type,
        "scoped_lesson_ids": assignment.scoped_lesson_ids,
        "is_published": assignment.is_published,
        "order_index": assignment.order_index,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
        "questions": [
            {
                "id": question.id,
                "assignment_id": question.assignment_id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "correct_answer_text": question.correct_answer_text if include_answer_key else None,
                "difficulty": question.difficulty,
                "purpose_type": question.purpose_type,
                "order_index": question.order_index,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
                "options": [
                    {
                        "id": option.id,
                        "question_id": option.question_id,
                        "option_text": option.option_text,
                        "is_correct": option.is_correct if include_answer_key else False,
                        "order_index": option.order_index,
                        "created_at": option.created_at,
                        "updated_at": option.updated_at,
                    }
                    for option in sorted(question.options, key=lambda option: option.order_index)
                ],
            }
            for question in sorted(assignment.questions, key=lambda question: question.order_index)
        ],
    }


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    assignment_data: AssignmentCreate,
):
    # Tạo bài tập mới thủ công.
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
        assignment_type=assignment_data.assignment_type,
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
    # Sinh bài tập nháp bằng LLM cho một buổi học.
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
        assignment_type=AssignmentType.PRACTICE,
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
    # Tạo bài tập ôn tập từ ngân hàng câu hỏi.
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
        assignment_type=AssignmentType.PRACTICE,
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


@router.post("/generate-test", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def generate_test_from_question_bank(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    payload: AssignmentGenerateTestRequest,
):
    # Tạo bài kiểm tra từ ngân hàng câu hỏi theo phạm vi.
    """Generate an unpublished course-level test from scoped question bank items."""
    check_course_owner(db, course_id, current_user)

    unique_lesson_ids = list(dict.fromkeys(payload.lesson_ids))
    if unique_lesson_ids:
        lesson_count = db.query(Lesson).filter(
            Lesson.course_id == course_id,
            Lesson.id.in_(unique_lesson_ids),
        ).count()
        if lesson_count != len(unique_lesson_ids):
            raise NotFoundException("One or more scoped lessons were not found in this course")

    try:
        selected_questions = select_test_questions_from_bank(
            db=db,
            course_id=course_id,
            question_count=payload.question_count,
            lesson_ids=unique_lesson_ids,
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

    assignment_title = (payload.title or "").strip() or "Bài kiểm tra"
    assignment = Assignment(
        course_id=course_id,
        lesson_id=None,
        title=assignment_title,
        assignment_type=AssignmentType.TEST,
        is_published=False,
        order_index=next_order,
    )
    db.add(assignment)
    db.flush()

    for index, lesson_id in enumerate(unique_lesson_ids):
        db.add(
            AssignmentLessonScope(
                assignment_id=assignment.id,
                lesson_id=lesson_id,
                order_index=index,
            )
        )

    question_types = choose_test_question_types(selected_questions)
    assignment_questions = [
        build_assignment_question_from_bank(question, question_types[question.id])
        for question in selected_questions
    ]
    add_questions_to_assignment(db, assignment, assignment_questions)

    db.commit()
    db.refresh(assignment)

    logger.info(
        "[Success] Test generated from question bank assignment_id=%s course_id=%s scoped_lessons=%s title=%s created_by=%s question_count=%s",
        assignment.id,
        assignment.course_id,
        len(unique_lesson_ids),
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
    # Lấy danh sách bài tập theo khóa học.
    """List assignments for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")

    query = db.query(Assignment).options(
        joinedload(Assignment.lesson_scopes),
        joinedload(Assignment.questions).joinedload(AssignmentQuestion.options),
    ).filter(Assignment.course_id == course_id)

    if current_user.role == UserRole.LEARNER or not include_unpublished:
        query = query.filter(Assignment.is_published.is_(True))

    assignments = query.order_by(Assignment.order_index).all()
    include_answer_key = current_user.role != UserRole.LEARNER
    return [
        serialize_assignment_for_response(assignment, include_answer_key=include_answer_key)
        for assignment in assignments
    ]


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    # Lấy chi tiết bài tập (ẩn đáp án với học viên).
    """Get assignment details."""
    assignment = check_assignment_access(db, assignment_id, current_user)

    if current_user.role == UserRole.LEARNER:
        if not assignment.is_published:
            raise NotFoundException("Assignment not found")
        return serialize_assignment_for_response(assignment, include_answer_key=False)

    if not assignment.is_published:
        is_owner = current_user.role == UserRole.ADMIN or assignment.course.instructor_id == current_user.id
        if not is_owner:
            raise NotFoundException("Assignment not found")

    return serialize_assignment_for_response(assignment, include_answer_key=True)


@router.get("/{assignment_id}/submission", response_model=SubmissionResponse)
async def get_my_submission(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    # Lấy bài nộp hiện tại của học viên.
    """Return the current learner's saved submission for an assignment."""
    if current_user.role != UserRole.LEARNER:
        raise ForbiddenException("Only learners can view their submissions")

    assignment = check_assignment_access(db, assignment_id, current_user)
    if not assignment.is_published:
        raise NotFoundException("Assignment not found")

    submission = (
        db.query(Submission)
        .options(
            joinedload(Submission.answers).joinedload(SubmissionAnswer.question),
            joinedload(Submission.answers).joinedload(SubmissionAnswer.selected_option),
        )
        .filter(
            Submission.assignment_id == assignment.id,
            Submission.user_id == current_user.id,
        )
        .first()
    )
    if not submission:
        raise NotFoundException("Submission not found")

    return submission


@router.post("/{assignment_id}/submit", response_model=SubmissionResponse)
async def submit_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    payload: AssignmentSubmitRequest,
    current_user: CurrentUser,
):
    # Lưu bài nộp và gọi AI để chấm/nhận xét.
    """Save a learner submission and generate per-question feedback."""
    if current_user.role != UserRole.LEARNER:
        raise ForbiddenException("Only learners can submit assignments")

    assignment = check_assignment_access(db, assignment_id, current_user)
    if not assignment.is_published:
        raise NotFoundException("Assignment not found")

    ordered_questions = sorted(assignment.questions, key=lambda question: question.order_index)
    answers_by_question = {answer.question_id: answer for answer in payload.answers}
    expected_question_ids = {question.id for question in ordered_questions}
    if set(answers_by_question) != expected_question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission must include exactly one answer for every question",
        )

    existing_submission = db.query(Submission).filter(
        Submission.assignment_id == assignment.id,
        Submission.user_id == current_user.id,
    ).first()
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submission already exists. Delete it before retaking.",
        )

    submission = Submission(
        assignment_id=assignment.id,
        user_id=current_user.id,
        status=SubmissionStatus.SUBMITTED,
        submitted_at=datetime.now(UTC),
    )
    db.add(submission)
    db.flush()

    saved_answers: list[SubmissionAnswer] = []
    for question in ordered_questions:
        answer_payload = answers_by_question[question.id]
        sorted_options = sorted(question.options, key=lambda option: option.order_index)
        correct_option = next((option for option in sorted_options if option.is_correct), None)
        correct_answer_text = question.correct_answer_text or (correct_option.option_text if correct_option else None)

        selected_option = None
        answer_text = (answer_payload.answer_text or "").strip() or None
        is_correct = None
        score_value = None

        if question.question_type == AssignmentQuestionType.MULTIPLE_CHOICE:
            if answer_payload.selected_option_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multiple-choice questions require selected_option_id",
                )
            selected_option = next(
                (option for option in sorted_options if option.id == answer_payload.selected_option_id),
                None,
            )
            if selected_option is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected option does not belong to the question",
                )
            answer_text = selected_option.option_text
            is_correct = selected_option.is_correct
            score_value = 1.0 if is_correct else 0.0
        elif not answer_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Essay questions require answer_text",
            )

        saved_answer = SubmissionAnswer(
            submission_id=submission.id,
            question_id=question.id,
            selected_option_id=selected_option.id if selected_option else None,
            answer_text=answer_text,
            is_correct=is_correct,
            score=score_value,
            correct_answer_text=correct_answer_text,
        )
        db.add(saved_answer)
        saved_answers.append(saved_answer)

    db.flush()

    feedback_result = AssignmentFeedbackService().generate_feedback(
        assignment=assignment,
        answers=saved_answers,
    )
    total_score = 0.0
    for answer in saved_answers:
        feedback = feedback_result.answers.get(answer.question_id)
        if feedback:
            answer.explanation = feedback.explanation
            answer.feedback = feedback.feedback
            if answer.question.question_type == AssignmentQuestionType.ESSAY:
                answer.score = feedback.score
                answer.is_correct = feedback.score >= 0.7
        total_score += float(answer.score or 0.0)

    submission.score = round((total_score / len(saved_answers)) * 100, 2) if saved_answers else 0
    submission.feedback = feedback_result.summary_feedback
    submission.status = SubmissionStatus.GRADED
    submission.graded_at = datetime.now(UTC)

    db.commit()
    db.refresh(submission)

    logger.info(
        "[Success] Assignment submitted assignment_id=%s submission_id=%s user=%s score=%s answer_count=%s",
        assignment.id,
        submission.id,
        current_user.email,
        submission.score,
        len(saved_answers),
    )

    return submission


@router.delete("/{assignment_id}/submission", response_model=Message)
async def delete_my_submission(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    # Xóa bài nộp để học viên làm lại.
    """Delete the current learner's saved submission so they can retake."""
    if current_user.role != UserRole.LEARNER:
        raise ForbiddenException("Only learners can delete their submissions")

    assignment = check_assignment_access(db, assignment_id, current_user)
    if not assignment.is_published:
        raise NotFoundException("Assignment not found")

    submission = db.query(Submission).filter(
        Submission.assignment_id == assignment.id,
        Submission.user_id == current_user.id,
    ).first()
    if not submission:
        raise NotFoundException("Submission not found")

    submission_id = submission.id
    db.delete(submission)
    db.commit()

    logger.info(
        "[Success] Assignment submission deleted assignment_id=%s submission_id=%s user=%s",
        assignment.id,
        submission_id,
        current_user.email,
    )

    return Message(message="Submission deleted successfully")


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    assignment_data: AssignmentUpdate,
    current_user: InstructorUser,
):
    # Cập nhật thông tin bài tập và câu hỏi.
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
    # Xóa bài tập.
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
    # Xuất bản bài tập.
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
