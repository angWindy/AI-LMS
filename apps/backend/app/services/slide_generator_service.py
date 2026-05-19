"""Service for generating lecture slides from lesson context."""
import json
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
from llm.config import LLMConfig
from llm.workflows.slide_generator import SlideGeneratorWorkflow

from app.core.config import settings
from app.models.course import Course
from app.models.lesson import Lesson

logger = logging.getLogger(__name__)


@dataclass
class SlideGenerationServiceResult:
    """Structured slide generation output."""

    ir_json: dict[str, Any]
    slides_json: dict[str, Any]
    provider: str
    model: str
    usage: dict[str, int] | None


class SlideGeneratorService:
    """Build prompt context and normalize generated lecture slides."""

    MAX_SLIDE_COUNT = 50
    RETRY_MAX_OUTPUT_TOKENS = 16384
    SLIDE_TYPES = {
        "title",
        "objectives",
        "concept",
        "comparison",
        "example",
        "summary",
        "quiz",
    }

    def __init__(self, workflow: SlideGeneratorWorkflow | None = None) -> None:
        config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            thinking_level=settings.LLM_THINKING_LEVEL,
            request_timeout_seconds=settings.LLM_REQUEST_TIMEOUT_SECONDS,
            google_api_key=settings.GOOGLE_AI_API_KEY,
        )
        self.workflow = workflow or SlideGeneratorWorkflow(config=config)

    def generate_slides(
        self,
        course: Course,
        lesson: Lesson,
        slide_count: int,
    ) -> SlideGenerationServiceResult:
        """Generate and validate lecture slides for one lesson."""
        if slide_count < 1 or slide_count > self.MAX_SLIDE_COUNT:
            raise ValueError(f"slide_count must be between 1 and {self.MAX_SLIDE_COUNT}.")

        if self.workflow.provider.provider_name == "mock":
            ir_json = self._build_mock_ir(course_title=course.title, lesson_title=lesson.title)
            slides_json = self._build_mock_slides(
                lesson_title=lesson.title,
                slide_count=slide_count,
            )
            return SlideGenerationServiceResult(
                ir_json=ir_json,
                slides_json=slides_json,
                provider="mock",
                model="mock-v1",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )

        course_context = self._build_course_context(course)
        lesson_context = self._build_lesson_context(lesson)

        try:
            ir_result = self.workflow.generate_document_ir(
                course_context=course_context,
                lesson_context=lesson_context,
                course_level=str(course.level),
            )
            ir_json = self._parse_ir(ir_result.text)

            slides_result = self.workflow.generate_slides_from_ir(
                ir_json=json.dumps(ir_json, ensure_ascii=False),
                slide_count=slide_count,
                course_level=str(course.level),
            )
            slides_json = self._parse_slides(
                raw_text=slides_result.text,
                expected_count=slide_count,
                ir_json=ir_json,
            )
        except ValueError:
            raise
        except Exception:
            logger.exception(
                "[Error][SlideGeneratorService] LLM call failed course_id=%s lesson_id=%s slide_count=%s",
                getattr(course, "id", None),
                getattr(lesson, "id", None),
                slide_count,
            )
            raise

        return SlideGenerationServiceResult(
            ir_json=ir_json,
            slides_json=slides_json,
            provider=slides_result.provider,
            model=slides_result.model,
            usage=slides_result.usage,
        )

    def render_pdf(
        self,
        slides_json: dict[str, Any],
        lesson_id: uuid.UUID,
        slide_deck_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Render generated slides JSON into a simple lecture PDF."""
        output_dir = Path(settings.STORAGE_PATH) / "slides" / str(lesson_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{slide_deck_id}.pdf"

        font_regular = self._find_font("DejaVuSans.ttf")
        font_bold = self._find_font("DejaVuSans-Bold.ttf")

        document = fitz.open()
        for slide in slides_json.get("slides", []):
            if not isinstance(slide, dict):
                continue
            page = document.new_page(width=960, height=540)
            self._draw_slide_page(
                page=page,
                slide=slide,
                title=str(slides_json.get("title", "")).strip(),
                font_regular=font_regular,
                font_bold=font_bold,
            )

        if len(document) == 0:
            page = document.new_page(width=960, height=540)
            self._insert_text(
                page,
                fitz.Rect(56, 56, 904, 180),
                "Slide bài giảng",
                font_size=30,
                font_path=font_bold,
            )

        document.save(output_path)
        document.close()

        relative_path = output_path.relative_to(Path(settings.STORAGE_PATH))
        return {
            "pdf_url": f"/storage/{relative_path}",
            "pdf_file_size": output_path.stat().st_size,
            "pdf_mime_type": "application/pdf",
        }

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
            f"Content: {self._truncate(lesson.content, 4000) or 'N/A'}",
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
            description = (getattr(material, "description", "") or "").strip()
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

    def _parse_ir(self, raw_text: str) -> dict[str, Any]:
        payload = self._extract_json_payload(raw_text)
        if not isinstance(payload, dict):
            raise ValueError("IR response JSON must be an object.")

        main_sections = payload.get("main_sections")
        if not isinstance(main_sections, list):
            raise ValueError("IR JSON must contain main_sections array.")

        for index, section in enumerate(main_sections, start=1):
            if not isinstance(section, dict):
                raise ValueError(f"IR main_sections #{index} must be an object.")
            try:
                section_id = int(section.get("id"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"IR main_sections #{index} has invalid id.") from exc
            if section_id != index:
                raise ValueError("IR main_sections.id must start at 1 and increase sequentially.")

        return payload

    def _parse_slides(
        self,
        raw_text: str,
        expected_count: int,
        ir_json: dict[str, Any],
    ) -> dict[str, Any]:
        payload = self._extract_json_payload(raw_text)
        if not isinstance(payload, dict):
            raise ValueError("Slides response JSON must be an object.")

        if payload.get("document_type") != "slides":
            raise ValueError('Slides JSON must contain document_type="slides".')

        raw_slides = payload.get("slides")
        if not isinstance(raw_slides, list):
            raise ValueError("Slides JSON must contain slides array.")

        if len(raw_slides) != expected_count:
            raise ValueError(
                f"LLM returned {len(raw_slides)} slides. Expected exactly {expected_count}."
            )

        valid_source_ids = {
            int(section["id"])
            for section in ir_json.get("main_sections", [])
            if isinstance(section, dict) and str(section.get("id", "")).isdigit()
        }

        for index, slide in enumerate(raw_slides, start=1):
            if not isinstance(slide, dict):
                raise ValueError(f"Slide #{index} must be a JSON object.")

            try:
                slide_id = int(slide.get("id"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Slide #{index} has invalid id.") from exc
            if slide_id != index:
                raise ValueError("Slide id must start at 1 and increase sequentially.")

            slide_type = str(slide.get("slide_type", "")).strip()
            if slide_type not in self.SLIDE_TYPES:
                raise ValueError(f"Slide #{index} has invalid slide_type '{slide_type}'.")

            content = slide.get("content")
            if not isinstance(content, list) or any(not str(item).strip() for item in content):
                raise ValueError(f"Slide #{index} content must contain non-empty bullet strings.")

            speaker_notes = slide.get("speaker_notes")
            if speaker_notes is not None and not str(speaker_notes).strip():
                raise ValueError(f"Slide #{index} speaker_notes must be a non-empty string if provided.")

            source_sections = slide.get("source_sections")
            if not isinstance(source_sections, list):
                raise ValueError(f"Slide #{index} source_sections must be an array.")
            invalid_ids = [
                item for item in source_sections if not isinstance(item, int) or item not in valid_source_ids
            ]
            if invalid_ids and valid_source_ids:
                raise ValueError(f"Slide #{index} has invalid source_sections: {invalid_ids}.")

        return payload

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
    def _build_mock_ir(course_title: str, lesson_title: str) -> dict[str, Any]:
        return {
            "document_title": lesson_title,
            "domain": course_title,
            "summary": f"Tom tat bai hoc {lesson_title}.",
            "learning_objectives": [f"Hieu noi dung chinh cua {lesson_title}."],
            "key_concepts": [],
            "main_sections": [
                {
                    "id": 1,
                    "heading": lesson_title,
                    "summary": f"Noi dung chinh cua {lesson_title}.",
                    "key_points": [f"Y chinh cua {lesson_title}."],
                    "examples": [],
                    "teaching_suggestions": [],
                    "possible_visuals": [],
                }
            ],
        }

    @staticmethod
    def _build_mock_slides(lesson_title: str, slide_count: int) -> dict[str, Any]:
        slides: list[dict[str, Any]] = []
        for index in range(1, slide_count + 1):
            slide_type = "title" if index == 1 else "summary" if index == slide_count else "concept"
            slides.append(
                {
                    "id": index,
                    "slide_type": slide_type,
                    "title": f"{lesson_title} - Slide {index}",
                    "content": [f"Noi dung chinh cho slide {index}."],
                    "speaker_notes": f"Giang vien trinh bay y chinh cua slide {index}.",
                    "source_sections": [1],
                }
            )
        return {
            "document_type": "slides",
            "title": lesson_title,
            "slides": slides,
        }

    @staticmethod
    def _find_font(filename: str) -> str | None:
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu") / filename,
            Path("/usr/local/share/fonts") / filename,
        ]
        return next((str(path) for path in candidates if path.exists()), None)

    def _draw_slide_page(
        self,
        page: fitz.Page,
        slide: dict[str, Any],
        title: str,
        font_regular: str | None,
        font_bold: str | None,
    ) -> None:
        page.draw_rect(fitz.Rect(0, 0, 960, 540), color=(0.94, 0.97, 1), fill=(0.94, 0.97, 1))
        page.draw_rect(fitz.Rect(28, 28, 932, 512), color=(0.86, 0.88, 0.91), fill=(1, 1, 1))

        slide_id = int(slide.get("id") or 0)
        slide_type = str(slide.get("slide_type", "")).strip()
        slide_title = str(slide.get("title") or title or "Slide bài giảng").strip()

        self._insert_text(
            page,
            fitz.Rect(56, 48, 852, 116),
            slide_title,
            font_size=24,
            font_path=font_bold,
            color=(0.05, 0.09, 0.16),
        )
        self._insert_text(
            page,
            fitz.Rect(820, 56, 904, 88),
            f"{slide_id}",
            font_size=16,
            font_path=font_bold,
            align=fitz.TEXT_ALIGN_RIGHT,
            color=(0.30, 0.36, 0.44),
        )
        if slide_type:
            self._insert_text(
                page,
                fitz.Rect(56, 102, 904, 130),
                slide_type.upper(),
                font_size=10,
                font_path=font_bold,
                color=(0.19, 0.39, 0.72),
            )

        bullets = [str(item).strip() for item in slide.get("content", []) if str(item).strip()]
        bullet_text = "\n".join(f"• {item}" for item in bullets[:8])
        self._insert_text(
            page,
            fitz.Rect(72, 150, 888, 340),
            bullet_text,
            font_size=16,
            font_path=font_regular,
            color=(0.10, 0.14, 0.20),
        )

        notes = str(slide.get("speaker_notes", "")).strip()
        if notes:
            page.draw_rect(
                fitz.Rect(56, 370, 904, 486),
                color=(0.88, 0.91, 0.95),
                fill=(0.97, 0.98, 0.99),
            )
            self._insert_text(
                page,
                fitz.Rect(76, 384, 884, 406),
                "Ghi chú giảng viên",
                font_size=11,
                font_path=font_bold,
                color=(0.22, 0.28, 0.36),
            )
            self._insert_text(
                page,
                fitz.Rect(76, 410, 884, 478),
                notes,
                font_size=11,
                font_path=font_regular,
                color=(0.30, 0.36, 0.44),
            )

    @staticmethod
    def _insert_text(
        page: fitz.Page,
        rect: fitz.Rect,
        text: str,
        font_size: float,
        font_path: str | None,
        color: tuple[float, float, float] = (0, 0, 0),
        align: int = fitz.TEXT_ALIGN_LEFT,
    ) -> None:
        kwargs = {
            "fontsize": font_size,
            "color": color,
            "align": align,
        }
        if font_path:
            kwargs["fontname"] = "dejavu"
            kwargs["fontfile"] = font_path
        page.insert_textbox(rect, text, **kwargs)
