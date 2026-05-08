"""Service for generating assignment questions from lesson context."""
import json
import logging
import re
from dataclasses import dataclass

from app.core.config import settings
from app.models.course import Course
from app.models.lesson import Lesson
from app.schemas.assignment import AssignmentOptionCreate, AssignmentQuestionCreate
from llm.config import LLMConfig
from llm.workflows.assignment_generator import (
    AssignmentGeneratorResult,
    AssignmentGeneratorWorkflow,
)


logger = logging.getLogger(__name__)


@dataclass
class AssignmentGenerationServiceResult:
    """Structured assignment generation output."""

    questions: list[AssignmentQuestionCreate]
    provider: str
    model: str
    usage: dict[str, int] | None


class AssignmentGeneratorService:
    """Build prompt context and normalize generated assignment questions."""

    MAX_QUESTION_COUNT = 100
    RETRY_MAX_OUTPUT_TOKENS = 8192

    def __init__(self, workflow: AssignmentGeneratorWorkflow | None = None) -> None:
        config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            thinking_level=settings.LLM_THINKING_LEVEL,
            request_timeout_seconds=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            google_api_key=settings.GOOGLE_AI_API_KEY,
        )
        self.workflow = workflow or AssignmentGeneratorWorkflow(config=config)

    def generate_questions(
        self,
        course: Course,
        lesson: Lesson,
        question_count: int,
    ) -> AssignmentGenerationServiceResult:
        """Generate and validate multiple-choice questions for one lesson."""
        if question_count < 1 or question_count > self.MAX_QUESTION_COUNT:
            raise ValueError(
                f"question_count must be between 1 and {self.MAX_QUESTION_COUNT}."
            )

        if self.workflow.provider.provider_name == "mock":
            questions = self._build_mock_questions(lesson_title=lesson.title, count=question_count)
            return AssignmentGenerationServiceResult(
                questions=questions,
                provider="mock",
                model="mock-v1",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )

        course_context = self._build_course_context(course)
        lesson_context = self._build_lesson_context(lesson)
        try:
            llm_result = self.workflow.run(
                question_count=question_count,
                course_context=course_context,
                lesson_context=lesson_context,
            )
        except Exception:
            logger.exception(
                "[Error][AssignmentGeneratorService] LLM call failed course_id=%s lesson_id=%s question_count=%s",
                getattr(course, "id", None),
                getattr(lesson, "id", None),
                question_count,
            )
            raise

        if not llm_result.text.strip():
            finish = (llm_result.finish_reason or "").upper()
            logger.error(
                "[Error][AssignmentGeneratorService] LLM returned empty response course_id=%s lesson_id=%s question_count=%s provider=%s model=%s finish_reason=%s",
                getattr(course, "id", None),
                getattr(lesson, "id", None),
                question_count,
                llm_result.provider,
                llm_result.model,
                llm_result.finish_reason,
            )
            if "RECITATION" in finish or "SAFETY" in finish or "PROHIBITED" in finish:
                raise RuntimeError(
                    f"LLM từ chối sinh nội dung do chính sách nội dung (finish_reason={llm_result.finish_reason}). "
                    "Vui lòng thử lại hoặc điều chỉnh nội dung bài học."
                )
            raise RuntimeError("LLM returned an empty response.")

        try:
            questions, final_result = self._parse_with_retry(
                llm_result=llm_result,
                course_context=course_context,
                lesson_context=lesson_context,
                question_count=question_count,
            )
        except ValueError:
            logger.exception(
                "[Error][AssignmentGeneratorService] Failed to parse LLM response course_id=%s lesson_id=%s question_count=%s provider=%s model=%s raw_text_preview=%.200r",
                getattr(course, "id", None),
                getattr(lesson, "id", None),
                question_count,
                llm_result.provider,
                llm_result.model,
                llm_result.text,
            )
            raise

        return AssignmentGenerationServiceResult(
            questions=questions,
            provider=final_result.provider,
            model=final_result.model,
            usage=final_result.usage,
        )

    def _parse_with_retry(
        self,
        llm_result: AssignmentGeneratorResult,
        course_context: str,
        lesson_context: str,
        question_count: int,
    ) -> tuple[list[AssignmentQuestionCreate], AssignmentGeneratorResult]:
        try:
            questions = self._parse_questions(llm_result.text, question_count)
            return questions, llm_result
        except ValueError as first_error:
            if not self._should_retry(first_error, llm_result.finish_reason):
                raise

            retry_result = self.workflow.run(
                question_count=question_count,
                course_context=course_context,
                lesson_context=lesson_context,
                max_output_tokens=self._retry_token_budget(question_count),
                temperature=0.0,
            )

            if not retry_result.text.strip():
                raise ValueError("LLM returned an empty response after retry.") from first_error

            questions = self._parse_questions(retry_result.text, question_count)
            return questions, retry_result

    @staticmethod
    def _should_retry(error: ValueError, finish_reason: str | None) -> bool:
        message = str(error)
        finish = (finish_reason or "").upper()
        message_upper = message.upper()
        return (
            "MAX_TOKENS" in finish
            or "JSON" in message_upper
            or "QUESTION #" in message_upper
            or "EXPECTED EXACTLY" in message_upper
        )

    def _retry_token_budget(self, question_count: int) -> int:
        budget = max(3000, question_count * 650)
        return min(budget, self.RETRY_MAX_OUTPUT_TOKENS)

    def _build_course_context(self, course: Course) -> str:
        lines = [
            f"Title: {course.title}",
            f"Description: {self._truncate(course.description, 1500) or 'N/A'}",
            f"Short description: {self._truncate(course.short_description, 500) or 'N/A'}",
            f"Category: {course.category or 'N/A'}",
            f"Level: {course.level or 'N/A'}",
            f"Language: {course.language or 'N/A'}",
        ]

        material_lines = self._material_context_lines(getattr(course, "materials", []), "course")
        if material_lines:
            lines.append("Course materials:")
            lines.extend(material_lines)

        return "\n".join(lines)

    def _build_lesson_context(self, lesson: Lesson) -> str:
        lines = [
            f"Title: {lesson.title}",
            f"Description: {self._truncate(lesson.description, 1000) or 'N/A'}",
            f"Content: {self._truncate(lesson.content, 2500) or 'N/A'}",
            f"Video URL: {lesson.video_url or 'N/A'}",
        ]

        material_lines = self._material_context_lines(getattr(lesson, "materials", []), "lesson")
        if material_lines:
            lines.append("Lesson materials:")
            lines.extend(material_lines)

        return "\n".join(lines)

    @staticmethod
    def _material_context_lines(materials: list, scope: str) -> list[str]:
        lines: list[str] = []
        for material in materials[:8]:
            title = (getattr(material, "title", "") or "").strip() or "Untitled"
            description = (
                getattr(material, "description", "") or ""
            ).strip()
            material_type = getattr(material, "type", "unknown")
            prefix = f"- [{scope}] {title} ({material_type})"
            if description:
                lines.append(f"{prefix}: {description[:400]}")
            else:
                lines.append(prefix)
        return lines

    @staticmethod
    def _truncate(value: str | None, max_chars: int) -> str:
        if not value:
            return ""
        cleaned = " ".join(value.split())
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[: max_chars - 3].rstrip() + "..."

    def _parse_questions(
        self,
        raw_text: str,
        expected_count: int,
    ) -> list[AssignmentQuestionCreate]:
        payload = self._extract_json_payload(raw_text)

        if isinstance(payload, dict):
            raw_questions = payload.get("questions")
        elif isinstance(payload, list):
            raw_questions = payload
        else:
            raise ValueError("LLM response JSON must be an object or an array.")

        if not isinstance(raw_questions, list):
            raise ValueError("JSON response must contain a questions array.")

        if len(raw_questions) != expected_count:
            raise ValueError(
                f"LLM returned {len(raw_questions)} questions. Expected exactly {expected_count}."
            )

        normalized_questions: list[AssignmentQuestionCreate] = []
        for index, raw_question in enumerate(raw_questions, start=1):
            if not isinstance(raw_question, dict):
                raise ValueError(f"Question #{index} must be a JSON object.")

            raw_id = raw_question.get("id")
            try:
                question_id = int(raw_id)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Question #{index} has invalid id. Expected integer {index}.") from exc
            if question_id != index:
                raise ValueError(
                    f"Question id must be sequential from 1..{expected_count}. "
                    f"Expected {index}, got {question_id}."
                )

            question_type = str(raw_question.get("type", "text")).strip().lower()
            if question_type != "text":
                raise ValueError(f"Question #{index} has invalid type '{question_type}'. Expected 'text'.")

            question_text = str(raw_question.get("question", "")).strip()
            if not question_text:
                raise ValueError(f"Question #{index} has empty question text.")

            explanation = str(raw_question.get("explanation", "")).strip()
            if not explanation:
                raise ValueError(f"Question #{index} has empty explanation.")
            explanation = self._normalize_explanation(explanation)

            raw_options = raw_question.get("options")
            if not isinstance(raw_options, list) or len(raw_options) != 4:
                raise ValueError(f"Question #{index} must include exactly 4 options.")

            options = [str(option).strip() for option in raw_options]
            if any(not option for option in options):
                raise ValueError(f"Question #{index} contains an empty option.")

            correct_answer = str(raw_question.get("correct_answer", "")).strip()
            correct_index = self._resolve_correct_index(correct_answer, options)

            normalized_questions.append(
                AssignmentQuestionCreate(
                    question_text=question_text,
                    explanation=explanation,
                    options=[
                        AssignmentOptionCreate(
                            option_text=option,
                            is_correct=option_index == correct_index,
                        )
                        for option_index, option in enumerate(options)
                    ],
                )
            )

        return normalized_questions

    @staticmethod
    def _resolve_correct_index(correct_answer: str, options: list[str]) -> int:
        if correct_answer in options:
            return options.index(correct_answer)

        normalized = correct_answer.upper().strip()
        letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
        if normalized in letter_map:
            return letter_map[normalized]

        if normalized.isdigit():
            index = int(normalized) - 1
            if 0 <= index < 4:
                return index

        raise ValueError("correct_answer must match one of the 4 options exactly.")

    @staticmethod
    def _normalize_explanation(explanation: str) -> str:
        compact = " ".join(explanation.split())
        if len(compact) > 280:
            compact = compact[:277].rstrip() + "..."
        return compact

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
            raise ValueError("LLM response does not contain valid JSON.")

        start_index = min(start_candidates)
        end_index = max(end_candidates)
        if end_index <= start_index:
            raise ValueError("LLM response does not contain valid JSON.")

        candidate = text[start_index : end_index + 1]
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse JSON from LLM response.") from exc

        if not isinstance(payload, (dict, list)):
            raise ValueError("LLM response JSON must be an object or an array.")

        return payload

    @staticmethod
    def _build_mock_questions(lesson_title: str, count: int) -> list[AssignmentQuestionCreate]:
        questions: list[AssignmentQuestionCreate] = []
        for index in range(1, count + 1):
            base = f"{lesson_title} - Cau hoi {index}"
            options = [
                f"{base} dap an A",
                f"{base} dap an B",
                f"{base} dap an C",
                f"{base} dap an D",
            ]
            questions.append(
                AssignmentQuestionCreate(
                    question_text=f"Noi dung cau hoi {index} cho bai hoc {lesson_title}?",
                    explanation=(
                        f"Dap an dung la phuong an A. Can nho y chinh cua bai hoc {lesson_title}."
                    ),
                    options=[
                        AssignmentOptionCreate(option_text=option, is_correct=option_index == 0)
                        for option_index, option in enumerate(options)
                    ],
                )
            )
        return questions
