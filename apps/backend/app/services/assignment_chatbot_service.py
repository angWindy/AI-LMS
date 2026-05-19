"""Backend orchestration for the assignment support chatbot."""
import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.ai_interaction import AIConversation
from app.models.assignment import Assignment, AssignmentQuestion
from app.models.user import User, UserRole
from app.services.chatbot_service import ChatbotService, ChatbotServiceResult
from llm.models import ChatMessage
from llm.prompts.assignment_chatbot import build_assignment_tutor_prompt


_ASSIGNMENT_CONTEXT_CACHE_MAX_SIZE = 128
_ASSIGNMENT_CONTEXT_CACHE: dict[tuple[uuid.UUID, str], str] = {}
_ASSIGNMENT_CONVERSATION_PREFIX = "Assignment support"


class AssignmentChatbotService:
    """Builds assignment tutoring context and delegates generation to ChatbotService."""

    def __init__(self, chatbot_service: ChatbotService | None = None) -> None:
        self.chatbot_service = chatbot_service or ChatbotService()

    def ask(
        self,
        db: Session,
        user: User,
        assignment_id: uuid.UUID,
        question: str,
        history: Sequence[ChatMessage] | None = None,
        conversation_id: uuid.UUID | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> ChatbotServiceResult:
        """Generate one guided hint for a learner working on an assignment."""
        assignment = self._get_assignment_for_user(
            db=db,
            assignment_id=assignment_id,
            user=user,
        )

        lesson = assignment.lesson
        course = assignment.course
        conversation_title = self._build_conversation_title(assignment)
        if conversation_id:
            self._validate_assignment_conversation(
                db=db,
                user_id=user.id,
                conversation_id=conversation_id,
                assignment_id=assignment.id,
            )

        assignment_context = self._get_cached_assignment_context(assignment)
        system_prompt = build_assignment_tutor_prompt(
            course_title=course.title if course else None,
            lesson_title=lesson.title if lesson else None,
            course_level=str(course.level) if course else None,
        )

        return self.chatbot_service.ask(
            db=db,
            user_id=user.id,
            question=question,
            history=history,
            system_prompt=system_prompt,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            course_id=assignment.course_id,
            lesson_id=assignment.lesson_id,
            context_docs=[assignment_context],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
            reuse_existing_conversation=False,
            enable_auto_rag=False,
            append_lms_prompt=False,
        )

    def preload_context(
        self,
        db: Session,
        user: User,
        assignment_id: uuid.UUID,
    ) -> dict[str, int | str]:
        """Validate access and warm the sanitized assignment context cache."""
        assignment = self._get_assignment_for_user(
            db=db,
            assignment_id=assignment_id,
            user=user,
        )
        assignment_context = self._get_cached_assignment_context(assignment)
        return {
            "assignment_id": str(assignment.id),
            "question_count": len(assignment.questions),
            "context_length": len(assignment_context),
        }

    def _get_assignment_for_user(
        self,
        db: Session,
        assignment_id: uuid.UUID,
        user: User,
    ) -> Assignment:
        assignment = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.course),
                joinedload(Assignment.lesson),
                joinedload(Assignment.questions).joinedload(AssignmentQuestion.options),
            )
            .filter(Assignment.id == assignment_id)
            .first()
        )
        if not assignment:
            raise ValueError("Assignment not found.")

        if user.role == UserRole.LEARNER:
            if not assignment.is_published:
                raise ValueError("Assignment is not published.")

        if user.role == UserRole.INSTRUCTOR and assignment.course.instructor_id != user.id:
            raise ValueError("Assignment not found.")

        return assignment

    def _build_assignment_context(self, assignment: Assignment) -> str:
        """Format assignment questions and options without answer keys."""
        lines = [
            "ASSIGNMENT_CONTEXT:",
            "The following assignment questions and options are visible to the learner.",
            "",
        ]

        ordered_questions = sorted(
            assignment.questions,
            key=lambda question: question.order_index,
        )
        for question_index, question in enumerate(ordered_questions, start=1):
            lines.append(f"Question {question_index}: {question.question_text.strip()}")
            sorted_options = sorted(
                question.options,
                key=lambda option: option.order_index,
            )
            for option_index, option in enumerate(sorted_options[:4]):
                option_label = chr(65 + option_index)
                lines.append(f"{option_label}. {option.option_text.strip()}")
            lines.append("")

        return "\n".join(lines).strip()

    def _get_cached_assignment_context(self, assignment: Assignment) -> str:
        cache_key = (assignment.id, self._assignment_cache_version(assignment))
        cached_context = _ASSIGNMENT_CONTEXT_CACHE.get(cache_key)
        if cached_context is not None:
            return cached_context

        context = self._build_assignment_context(assignment)
        if len(_ASSIGNMENT_CONTEXT_CACHE) >= _ASSIGNMENT_CONTEXT_CACHE_MAX_SIZE:
            oldest_key = next(iter(_ASSIGNMENT_CONTEXT_CACHE))
            _ASSIGNMENT_CONTEXT_CACHE.pop(oldest_key, None)

        _ASSIGNMENT_CONTEXT_CACHE[cache_key] = context
        return context

    def _assignment_cache_version(self, assignment: Assignment) -> str:
        timestamps = [assignment.updated_at]
        for question in assignment.questions:
            timestamps.append(question.updated_at)
            timestamps.extend(option.updated_at for option in question.options)

        valid_timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
        if not valid_timestamps:
            return "unversioned"

        return max(valid_timestamps).isoformat()

    def _build_conversation_title(self, assignment: Assignment) -> str:
        return f"{_ASSIGNMENT_CONVERSATION_PREFIX} [{assignment.id}]: {assignment.title}"

    def _validate_assignment_conversation(
        self,
        db: Session,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        assignment_id: uuid.UUID,
    ) -> None:
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            )
            .first()
        )
        expected_marker = f"[{assignment_id}]"
        if not conversation or expected_marker not in (conversation.title or ""):
            raise ValueError("Conversation does not belong to this assignment.")
