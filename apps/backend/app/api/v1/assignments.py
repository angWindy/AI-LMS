"""
Assignment and Submission API endpoints.
"""
from datetime import datetime, timezone
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
from app.models.assignment import Assignment
from app.models.submission import Submission, SubmissionStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionGrade,
    SubmissionResponse,
    SubmissionDetailResponse,
)
from app.schemas.common import Message, PaginatedResponse
from app.utils.file_handler import file_handler

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
    """Check access to assignment."""
    assignment = db.query(Assignment).options(
        joinedload(Assignment.course)
    ).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise NotFoundException("Assignment not found")
    
    if require_owner:
        if user.role != UserRole.ADMIN and assignment.course.instructor_id != user.id:
            raise ForbiddenException("Only course instructor or admin can perform this action")
    
    return assignment


# ============ ASSIGNMENT CRUD ============

@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    db: DBSession,
    current_user: InstructorUser,
    course_id: uuid.UUID,
    assignment_data: AssignmentCreate,
):
    """Create a new assignment for a course."""
    course = check_course_owner(db, course_id, current_user)
    
    # Validate lesson if provided
    if assignment_data.lesson_id:
        lesson = db.query(Lesson).filter(
            Lesson.id == assignment_data.lesson_id,
            Lesson.course_id == course_id
        ).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson not found in this course"
            )
    
    # Get next order index
    max_order = db.query(func.max(Assignment.order_index)).filter(
        Assignment.course_id == course_id
    ).scalar()
    next_order = (max_order or 0) + 1
    
    # Create assignment
    assignment = Assignment(
        course_id=course_id,
        lesson_id=assignment_data.lesson_id,
        title=assignment_data.title,
        description=assignment_data.description,
        instructions=assignment_data.instructions,
        due_date=assignment_data.due_date,
        max_score=assignment_data.max_score,
        allow_late_submission=assignment_data.allow_late_submission,
        late_penalty_percent=assignment_data.late_penalty_percent,
        order_index=next_order,
    )
    
    db.add(assignment)
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
    # Verify course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise NotFoundException("Course not found")
    
    # Build query
    query = db.query(Assignment).filter(Assignment.course_id == course_id)
    
    # Filter unpublished unless instructor/admin
    if not include_unpublished or current_user.role == UserRole.LEARNER:
        query = query.filter(Assignment.is_published == True)
    
    assignments = query.order_by(Assignment.order_index).all()
    
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get assignment details."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise NotFoundException("Assignment not found")
    
    # Check if published or user has special access
    if not assignment.is_published:
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
            raise NotFoundException("Assignment not found")
    
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    assignment_data: AssignmentUpdate,
    current_user: InstructorUser,
):
    """Update an assignment."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)
    
    # Update fields
    update_data = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assignment, field, value)
    
    db.commit()
    db.refresh(assignment)
    
    return assignment


@router.delete("/{assignment_id}", response_model=Message)
async def delete_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: InstructorUser,
):
    """Delete an assignment and all submissions."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)
    
    # Delete submission files
    submissions = db.query(Submission).filter(Submission.assignment_id == assignment_id).all()
    for submission in submissions:
        if submission.file_url:
            file_handler.delete_file(submission.file_url)
    
    # Delete assignment (cascades to submissions)
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


# ============ SUBMISSIONS ============

@router.post("/{assignment_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Submit an assignment (student)."""
    assignment = db.query(Assignment).options(
        joinedload(Assignment.course)
    ).filter(Assignment.id == assignment_id).first()
    
    if not assignment:
        raise NotFoundException("Assignment not found")
    
    if not assignment.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit to unpublished assignment"
        )
    
    # Check enrollment
    enrollment = db.query(Enrollment).filter(
        Enrollment.course_id == assignment.course_id,
        Enrollment.user_id == current_user.id,
        Enrollment.status == EnrollmentStatus.ACTIVE
    ).first()
    
    if not enrollment and current_user.role == UserRole.LEARNER:
        raise ForbiddenException("You must be enrolled to submit")
    
    # Check for existing submission
    existing = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.user_id == current_user.id
    ).first()
    
    if existing and existing.status == SubmissionStatus.GRADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify graded submission"
        )
    
    # Check late submission
    now = datetime.now(timezone.utc)
    is_late = False
    if assignment.due_date and now > assignment.due_date:
        if not assignment.allow_late_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment submission deadline has passed"
            )
        is_late = True
    
    # Handle file upload
    file_url = None
    file_name = None
    file_size = None
    
    if file and file.filename:
        file_info = await file_handler.save_submission_file(
            file, str(assignment_id), str(current_user.id)
        )
        file_url = file_info["file_url"]
        file_name = file_info["file_name"]
        file_size = file_info["file_size"]
    
    if existing:
        # Update existing submission
        if existing.file_url and file_url:
            file_handler.delete_file(existing.file_url)
        
        existing.content = content or existing.content
        if file_url:
            existing.file_url = file_url
            existing.file_name = file_name
            existing.file_size = file_size
        existing.status = SubmissionStatus.SUBMITTED
        existing.submitted_at = now
        existing.is_late = is_late
        
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new submission
        submission = Submission(
            assignment_id=assignment_id,
            user_id=current_user.id,
            content=content,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            status=SubmissionStatus.SUBMITTED,
            is_late=is_late,
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        return submission


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionDetailResponse])
async def list_submissions(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: InstructorUser,
):
    """List all submissions for an assignment (instructor only)."""
    assignment = check_assignment_access(db, assignment_id, current_user, require_owner=True)
    
    submissions = db.query(Submission).options(
        joinedload(Submission.user)
    ).filter(Submission.assignment_id == assignment_id).all()
    
    result = []
    for sub in submissions:
        result.append(SubmissionDetailResponse(
            id=sub.id,
            assignment_id=sub.assignment_id,
            user_id=sub.user_id,
            content=sub.content,
            file_url=sub.file_url,
            file_name=sub.file_name,
            file_size=sub.file_size,
            status=sub.status.value if hasattr(sub.status, 'value') else sub.status,
            score=sub.score,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
            graded_at=sub.graded_at,
            is_late=sub.is_late,
            user_name=sub.user.full_name,
            user_email=sub.user.email,
        ))
    
    return result


@router.get("/{assignment_id}/my-submission", response_model=SubmissionResponse)
async def get_my_submission(
    db: DBSession,
    assignment_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get current user's submission for an assignment."""
    submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise NotFoundException("No submission found")
    
    return submission


@router.post("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    db: DBSession,
    submission_id: uuid.UUID,
    grade_data: SubmissionGrade,
    current_user: InstructorUser,
):
    """Grade a submission (instructor only)."""
    submission = db.query(Submission).options(
        joinedload(Submission.assignment).joinedload(Assignment.course)
    ).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise NotFoundException("Submission not found")
    
    # Check ownership
    course = submission.assignment.course
    if current_user.role != UserRole.ADMIN and course.instructor_id != current_user.id:
        raise ForbiddenException("Only course instructor or admin can grade")
    
    # Validate score
    max_score = submission.assignment.max_score
    if grade_data.score < 0 or grade_data.score > max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {max_score}"
        )
    
    # Apply late penalty if applicable
    final_score = grade_data.score
    if submission.is_late and submission.assignment.late_penalty_percent > 0:
        penalty = grade_data.score * (submission.assignment.late_penalty_percent / 100)
        final_score = max(0, grade_data.score - penalty)
    
    # Update submission
    submission.score = final_score
    submission.feedback = grade_data.feedback
    submission.status = SubmissionStatus.GRADED
    submission.graded_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(submission)
    
    return submission


@router.get("/submissions/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(
    db: DBSession,
    submission_id: uuid.UUID,
    current_user: CurrentUser,
):
    """Get submission details."""
    submission = db.query(Submission).options(
        joinedload(Submission.user),
        joinedload(Submission.assignment).joinedload(Assignment.course)
    ).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise NotFoundException("Submission not found")
    
    # Check access: owner, instructor, or admin
    is_owner = submission.user_id == current_user.id
    is_instructor = submission.assignment.course.instructor_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not (is_owner or is_instructor or is_admin):
        raise ForbiddenException("You don't have access to this submission")
    
    return SubmissionDetailResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        user_id=submission.user_id,
        content=submission.content,
        file_url=submission.file_url,
        file_name=submission.file_name,
        file_size=submission.file_size,
        status=submission.status.value if hasattr(submission.status, 'value') else submission.status,
        score=submission.score,
        feedback=submission.feedback,
        submitted_at=submission.submitted_at,
        graded_at=submission.graded_at,
        is_late=submission.is_late,
        user_name=submission.user.full_name,
        user_email=submission.user.email,
    )
