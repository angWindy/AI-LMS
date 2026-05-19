"""Service for generating post-submission assignment feedback."""

import json
import logging
import re
import uuid
from dataclasses import dataclass

from llm.config import LLMConfig
from llm.workflows.assignment_feedback import AssignmentFeedbackWorkflow

from app.core.config import settings
from app.models.assignment import Assignment, AssignmentQuestionType
from app.models.submission import SubmissionAnswer

logger = logging.getLogger(__name__)


@dataclass
class AnswerFeedback:
    """Normalized feedback for one submitted answer."""

    question_id: uuid.UUID
    explanation: str
    feedback: str
    score: float


@dataclass
class AssignmentFeedback:
    """Normalized feedback output."""

    summary_feedback: str
    answers: dict[uuid.UUID, AnswerFeedback]
    provider: str
    model: str
    usage: dict[str, int] | None


class AssignmentFeedbackService:
    """Build context and normalize LLM feedback for submitted assignments."""

    def __init__(self, workflow: AssignmentFeedbackWorkflow | None = None) -> None:
        config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            thinking_level=settings.LLM_THINKING_LEVEL,
            request_timeout_seconds=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            google_api_key=settings.GOOGLE_AI_API_KEY,
        )
        self.workflow = workflow or AssignmentFeedbackWorkflow(config=config)

    def generate_feedback(
        self,
        assignment: Assignment,
        answers: list[SubmissionAnswer],
    ) -> AssignmentFeedback:
        """Generate feedback for a submitted assignment."""
        if self.workflow.provider.provider_name == "mock":
            return self._mock_feedback(answers)

        course_context = self._build_course_context(assignment)
        scope_context = self._build_scope_context(assignment)
        submission_context = self._build_submission_context(answers)

        try:
            result = self.workflow.run(
                course_context=course_context,
                scope_context=scope_context,
                submission_context=submission_context,
                course_level=str(assignment.course.level),
            )
        except Exception:
            logger.exception(
                "[Error][AssignmentFeedbackService] LLM call failed assignment_id=%s answer_count=%s",
                assignment.id,
                len(answers),
            )
            return self._fallback_feedback(answers)

        if not result.text.strip():
            return self._fallback_feedback(answers)

        try:
            parsed = self._parse_feedback(result.text, answers)
        except ValueError:
            logger.exception(
                "[Error][AssignmentFeedbackService] Failed to parse LLM feedback assignment_id=%s raw_text_preview=%.200r",
                assignment.id,
                result.text,
            )
            parsed = self._fallback_feedback(answers)

        parsed.provider = result.provider
        parsed.model = result.model
        parsed.usage = result.usage
        return parsed

    def _build_course_context(self, assignment: Assignment) -> str:
        course = assignment.course
        return "\n".join(
            [
                f"Title: {course.title}",
                f"Description: {self._truncate(course.description, 1200) or 'N/A'}",
                f"Short description: {self._truncate(course.short_description, 500) or 'N/A'}",
                f"Category: {course.category or 'N/A'}",
                f"Level: {course.level or 'N/A'}",
                f"Language: {course.language or 'N/A'}",
            ]
        )

    def _build_scope_context(self, assignment: Assignment) -> str:
        if assignment.lesson_id and assignment.lesson:
            return "\n".join(
                [
                    "Mode: review assignment",
                    f"Lesson: {assignment.lesson.title}",
                    f"Lesson description: {self._truncate(assignment.lesson.description, 800) or 'N/A'}",
                    f"Lesson content: {self._truncate(assignment.lesson.content, 1800) or 'N/A'}",
                ]
            )

        scope_lines = [
            "Mode: course-level test",
            "Scoped lessons:",
        ]
        for scope in sorted(assignment.lesson_scopes, key=lambda item: item.order_index):
            lesson = scope.lesson
            scope_lines.append(
                f"- {lesson.title}: {self._truncate(lesson.description or lesson.content, 700) or 'N/A'}"
            )
        if len(scope_lines) == 2:
            scope_lines.append("- Whole course question bank")
        return "\n".join(scope_lines)

    def _build_submission_context(self, answers: list[SubmissionAnswer]) -> str:
        items: list[dict[str, object]] = []
        for answer in answers:
            question = answer.question
            sorted_options = sorted(question.options, key=lambda option: option.order_index)
            correct_option = next((option for option in sorted_options if option.is_correct), None)
            selected_option = answer.selected_option
            items.append(
                {
                    "question_id": str(question.id),
                    "question_type": question.question_type.value,
                    "difficulty": question.difficulty.value,
                    "question": question.question_text,
                    "options": [
                        {
                            "id": str(option.id),
                            "text": option.option_text,
                            "is_correct": option.is_correct,
                        }
                        for option in sorted_options
                    ],
                    "correct_answer": question.correct_answer_text
                    or (correct_option.option_text if correct_option else ""),
                    "learner_answer": answer.answer_text
                    or (selected_option.option_text if selected_option else ""),
                    "auto_is_correct": answer.is_correct,
                }
            )
        return json.dumps(items, ensure_ascii=False)

    def _parse_feedback(
        self,
        raw_text: str,
        answers: list[SubmissionAnswer],
    ) -> AssignmentFeedback:
        payload = self._extract_json_payload(raw_text)
        if not isinstance(payload, dict):
            raise ValueError("Feedback response must be a JSON object.")

        raw_answers = payload.get("answers")
        if not isinstance(raw_answers, list):
            raise ValueError("Feedback response must include an answers array.")

        expected_ids = {answer.question_id for answer in answers}
        parsed_answers: dict[uuid.UUID, AnswerFeedback] = {}
        for raw_answer in raw_answers:
            if not isinstance(raw_answer, dict):
                continue
            try:
                question_id = uuid.UUID(str(raw_answer.get("question_id")))
            except (TypeError, ValueError):
                continue
            if question_id not in expected_ids:
                continue
            parsed_answers[question_id] = AnswerFeedback(
                question_id=question_id,
                explanation=str(raw_answer.get("explanation") or "").strip(),
                feedback=str(raw_answer.get("feedback") or "").strip(),
                score=self._coerce_score(raw_answer.get("score")),
            )

        for answer in answers:
            if answer.question_id not in parsed_answers:
                parsed_answers[answer.question_id] = self._fallback_answer_feedback(answer)

        return AssignmentFeedback(
            summary_feedback=str(payload.get("summary_feedback") or "").strip(),
            answers=parsed_answers,
            provider="unknown",
            model="unknown",
            usage=None,
        )

    @staticmethod
    def _extract_json_payload(raw_text: str) -> dict | list:
        text = raw_text.strip()
        fenced_match = re.search(
            r"```(?:json)?\s*(\{[\s\S]*\}|\[[\s\S]*\])\s*```",
            text,
            flags=re.IGNORECASE,
        )
        if fenced_match:
            text = fenced_match.group(1).strip()

        try:
            payload = json.loads(text)
            if isinstance(payload, (dict, list)):
                return payload
        except json.JSONDecodeError:
            pass

        start_candidates = [idx for idx in [text.find("{"), text.find("[")] if idx >= 0]
        end_candidates = [idx for idx in [text.rfind("}"), text.rfind("]")] if idx >= 0]
        if not start_candidates or not end_candidates:
            raise ValueError("Feedback response does not contain valid JSON.")

        candidate = text[min(start_candidates) : max(end_candidates) + 1]
        payload = json.loads(candidate)
        if not isinstance(payload, (dict, list)):
            raise ValueError("Feedback response JSON must be object or array.")
        return payload

    def _fallback_feedback(self, answers: list[SubmissionAnswer]) -> AssignmentFeedback:
        return AssignmentFeedback(
            summary_feedback="Hệ thống đã lưu bài làm. Nhận xét AI tạm thời chưa khả dụng.",
            answers={
                answer.question_id: self._fallback_answer_feedback(answer)
                for answer in answers
            },
            provider="fallback",
            model="fallback",
            usage=None,
        )

    def _mock_feedback(self, answers: list[SubmissionAnswer]) -> AssignmentFeedback:
        return AssignmentFeedback(
            summary_feedback="Bài làm đã được chấm bằng mock feedback.",
            answers={
                answer.question_id: AnswerFeedback(
                    question_id=answer.question_id,
                    explanation="Giải thích mock cho đáp án đúng.",
                    feedback=(
                        "Câu trả lời đạt yêu cầu."
                        if answer.is_correct
                        else "Cần đối chiếu lại với đáp án chuẩn và bổ sung lập luận."
                    ),
                    score=1.0 if answer.is_correct else 0.5,
                )
                for answer in answers
            },
            provider="mock",
            model="mock-v1",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    def _fallback_answer_feedback(self, answer: SubmissionAnswer) -> AnswerFeedback:
        question = answer.question
        if question.question_type == AssignmentQuestionType.MULTIPLE_CHOICE:
            explanation = "Đáp án đúng được xác định từ đáp án chuẩn của bài."
            feedback = "Bạn đã chọn đúng." if answer.is_correct else "Bạn cần xem lại lựa chọn và lý do của đáp án đúng."
            score = 1.0 if answer.is_correct else 0.0
        else:
            explanation = "Đáp án chuẩn đã được lưu để giảng viên hoặc AI đối chiếu."
            feedback = "Bài tự luận đã được ghi nhận. Nhận xét chi tiết sẽ được bổ sung khi AI khả dụng."
            score = 0.0

        return AnswerFeedback(
            question_id=answer.question_id,
            explanation=explanation,
            feedback=feedback,
            score=score,
        )

    @staticmethod
    def _coerce_score(value: object) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, score))

    @staticmethod
    def _truncate(value: str | None, max_chars: int) -> str:
        if not value:
            return ""
        cleaned = " ".join(value.split())
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[: max_chars - 3].rstrip() + "..."
