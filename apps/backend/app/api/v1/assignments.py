"""
Assignment API endpoints.
"""
from typing import List
import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.core.dependencies import DBSession, CurrentUser, InstructorUser
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.assignment import Assignment, AssignmentQuestion, AssignmentOption
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentQuestionCreate,
)
from app.schemas.common import Message

router = APIRouter(prefix="/assignments", tags=["Assignments"])


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


def add_questions_to_assignment(db: DBSession, assignment: Assignment, questions_data: List[AssignmentQuestionCreate]):
    """Attach full question tree to assignment."""
    for question_index, question_data in enumerate(questions_data):
        question = AssignmentQuestion(
            assignment_id=assignment.id,
            question_text=question_data.question_text,
            explanation=question_data.explanation,
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
        order_index=next_order,
    )

    db.add(assignment)
    db.flush()

    add_questions_to_assignment(db, assignment, assignment_data.questions)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.get("", response_model=List[AssignmentResponse])
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

    if current_user.role == UserRole.LEARNER:
        is_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.user_id == current_user.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        ).first() is not None

        if not is_enrolled:
            raise ForbiddenException("You must be enrolled in this course")

    if not include_unpublished or current_user.role == UserRole.LEARNER:
        query = query.filter(Assignment.is_published == True)

    return query.order_by(Assignment.order_index).all()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get assignment details."""
    assignment = check_assignment_access(db, assignment_id, current_user)

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

    return assignment


@router.delete("/{assignment_id}", response_model=Message)
async def delete_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete an assignment."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)

    db.delete(assignment)
    db.commit()

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

    return assignment
