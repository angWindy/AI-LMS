"""Chatbot orchestration service with future-ready extension points."""
import base64
import binascii
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
import uuid
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_interaction import AIConversation, AIMessage
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.rag import RAGDocument
from llm.config import LLMConfig
from llm.models import ChatMessage, ImageInput
from llm.prompts.chatbot import build_lms_chatbot_prompt
from llm.rag.context_builder import ContextBuilder, DefaultContextBuilder
from llm.workflows.chatbot import ChatbotResult, ChatbotWorkflow


logger = logging.getLogger(__name__)


@dataclass
class ChatbotServiceResult:
    """Service result with persisted conversation metadata."""

    conversation_id: uuid.UUID
    conversation_title: str | None
    result: ChatbotResult
    image_rule_matched: bool
    image_input_count: int
    image_used_count: int


@dataclass
class LMSChatScope:
    """Resolved course/lesson metadata for one chatbot turn."""

    course_id: uuid.UUID | None = None
    course_title: str | None = None
    course_level: str | None = None
    lesson_id: uuid.UUID | None = None
    lesson_title: str | None = None
    has_lesson_rag_documents: bool = False
    has_course_rag_documents: bool = False


class ChatbotService:
    """Coordinates prompt assembly and delegates text generation to a provider."""

    MAX_CONVERSATION_HISTORY_MESSAGES = 40
    MAX_CONTEXT_HISTORY_MESSAGES = 12
    MAX_CONTEXT_HISTORY_CHARS = 6000
    MAX_CONTEXT_HISTORY_MESSAGE_CHARS = 800
    MAX_IMAGE_BYTES = 10 * 1024 * 1024
    ALLOWED_IMAGE_MIME_TYPES = {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }

    def __init__(
        self,
        workflow: ChatbotWorkflow | None = None,
        context_builder: ContextBuilder | None = None,
        rag_service: Any | None = None,
    ) -> None:
        config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
            thinking_level=settings.LLM_THINKING_LEVEL,
            google_api_key=settings.GOOGLE_AI_API_KEY,
        )
        self.workflow = workflow or ChatbotWorkflow(
            config=config,
            context_builder=context_builder or DefaultContextBuilder(),
        )
        self.rag_service = rag_service

    def ask(
        self,
        db: Session,
        user_id: uuid.UUID,
        question: str,
        history: Sequence[ChatMessage] | None = None,
        system_prompt: str | None = None,
        conversation_id: uuid.UUID | None = None,
        conversation_title: str | None = None,
        course_id: uuid.UUID | None = None,
        lesson_id: uuid.UUID | None = None,
        context_docs: Sequence[str] | None = None,
        image_contexts: Sequence[str] | None = None,
        teaching_images: Sequence[dict[str, str | None]] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
        reuse_existing_conversation: bool = True,
        enable_auto_rag: bool = True,
        append_lms_prompt: bool = True,
    ) -> ChatbotServiceResult:
        # Tạo câu trả lời cho chatbot, đồng thời lưu lại lịch sử hội thoại.
        """Generate one assistant answer and persist the turn into conversation history."""
        if conversation_id and (course_id is None or lesson_id is None):
            existing_conversation = (
                db.query(AIConversation)
                .filter(
                    AIConversation.id == conversation_id,
                    AIConversation.user_id == user_id,
                )
                .first()
            )
            if existing_conversation:
                course_id = course_id or existing_conversation.course_id
                lesson_id = lesson_id or existing_conversation.lesson_id

        scope = self._resolve_lms_scope(
            db=db,
            course_id=course_id,
            lesson_id=lesson_id,
        )

        conversation = self._get_or_create_conversation(
            db=db,
            user_id=user_id,
            question=question,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            course_id=scope.course_id,
            lesson_id=scope.lesson_id,
            reuse_existing=reuse_existing_conversation,
        )

        persisted_history = self._load_conversation_history(db, conversation.id)
        runtime_history = list(persisted_history)
        if not conversation_id and history:
            runtime_history.extend(history)
        conversation_history_context = self._format_conversation_history_context(
            runtime_history
        )

        incoming_teaching_images = list(teaching_images or [])
        image_rule_matched = _need_teaching_image_strict(question)
        image_mode_active = image_rule_matched
        selected_teaching_images = (
            incoming_teaching_images if image_rule_matched else []
        )

        prepared_images, image_contexts_from_images = self._prepare_teaching_images(
            selected_teaching_images
        )
        merged_image_contexts = [
            *(image_contexts or []),
            *image_contexts_from_images,
        ]

        if incoming_teaching_images and not image_rule_matched:
            logger.debug(
                "[Debug] Chatbot service skipped teaching images by rule user_id=%s conversation_id=%s image_input_count=%s",
                user_id,
                conversation.id,
                len(incoming_teaching_images),
            )

        if image_mode_active and enable_auto_rag:
            logger.debug(
                "[Debug] Chatbot service skipped RAG because image rule matched user_id=%s conversation_id=%s",
                user_id,
                conversation.id,
            )

        auto_rag_context = (
            self._build_auto_rag_context(
                db=db,
                question=question,
                scope=scope,
            )
            if enable_auto_rag and not image_mode_active
            else []
        )
        explicit_context_docs = [] if image_mode_active else list(context_docs or [])
        merged_context_docs = [
            *auto_rag_context,
            *explicit_context_docs,
        ]
        effective_system_prompt = (
            _merge_optional_text(
                system_prompt,
                build_lms_chatbot_prompt(
                    course_title=scope.course_title,
                    lesson_title=scope.lesson_title,
                    course_level=scope.course_level,
                ),
            )
            if append_lms_prompt
            else system_prompt
        )

        llm_result = self.workflow.run(
            question=question,
            history=runtime_history,
            system_prompt=effective_system_prompt,
            rag_context=merged_context_docs,
            image_contexts=merged_image_contexts,
            conversation_history_context=conversation_history_context,
            images=prepared_images,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )

        logger.debug(
            "[Debug] Chatbot service assembled request provider=%s model=%s user_id=%s conversation_id=%s context_mode=%s image_rule_matched=%s has_image_input=%s image_input_count=%s image_used_count=%s rag_context_count=%s merged_image_context_count=%s conversation_history_context_count=%s",
            llm_result.provider,
            llm_result.model,
            user_id,
            conversation.id,
            "image" if image_mode_active else "rag_or_lms",
            image_rule_matched,
            len(incoming_teaching_images) > 0,
            len(incoming_teaching_images),
            len(prepared_images),
            len(merged_context_docs),
            len(merged_image_contexts),
            len(conversation_history_context),
        )

        messages_to_save: list[AIMessage] = []
        if merged_image_contexts:
            messages_to_save.append(
                AIMessage(
                    conversation_id=conversation.id,
                    role="system",
                    content=_format_image_context_message(merged_image_contexts),
                )
            )
        messages_to_save.append(
            AIMessage(
                conversation_id=conversation.id,
                role="user",
                content=question,
            )
        )
        messages_to_save.append(
            AIMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=llm_result.answer,
                tokens_used=(llm_result.usage or {}).get("total_tokens"),
                model_version=llm_result.model,
            )
        )

        conversation.updated_at = datetime.now(timezone.utc)
        for message in messages_to_save:
            db.add(message)
        db.commit()

        return ChatbotServiceResult(
            conversation_id=conversation.id,
            conversation_title=conversation.title,
            result=llm_result,
            image_rule_matched=image_rule_matched,
            image_input_count=len(incoming_teaching_images),
            image_used_count=len(prepared_images),
        )

    def list_conversations(
        self,
        db: Session,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[AIConversation]:
        # Lấy danh sách hội thoại gần nhất của người dùng.
        """List recent conversations for a learner/instructor."""
        return (
            db.query(AIConversation)
            .filter(AIConversation.user_id == user_id)
            .order_by(desc(AIConversation.updated_at))
            .limit(limit)
            .all()
        )

    def list_messages(
        self,
        db: Session,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        limit: int = 100,
    ) -> list[AIMessage]:
        # Trả về các tin nhắn thuộc một hội thoại của người dùng.
        """List messages for a conversation that belongs to the user."""
        conversation = (
            db.query(AIConversation)
            .filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            )
            .first()
        )
        if not conversation:
            raise ValueError("Conversation not found.")

        messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation_id)
            .order_by(desc(AIMessage.created_at))
            .limit(limit)
            .all()
        )
        messages.reverse()
        return messages

    def _load_conversation_history(
        self,
        db: Session,
        conversation_id: uuid.UUID,
    ) -> list[ChatMessage]:
        rows = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation_id)
            .order_by(desc(AIMessage.created_at))
            .limit(self.MAX_CONVERSATION_HISTORY_MESSAGES)
            .all()
        )
        rows.reverse()
        return [ChatMessage(role=row.role, content=row.content) for row in rows]

    def _format_conversation_history_context(
        self,
        history: Sequence[ChatMessage],
    ) -> list[str]:
        # Rút gọn lịch sử chat để đưa vào context cho lượt trả lời.
        """Format recent non-system turns as compact context for continuity."""
        selected_messages = [
            message
            for message in history
            if message.role in {"user", "assistant"} and message.content.strip()
        ][-self.MAX_CONTEXT_HISTORY_MESSAGES :]
        if not selected_messages:
            return []

        lines = ["Recent conversation history, oldest to newest:"]
        total_chars = len(lines[0])
        role_labels = {
            "user": "Learner",
            "assistant": "Assistant",
        }
        for message in selected_messages:
            content = self._truncate_history_message(
                " ".join(message.content.split())
            )
            if not content:
                continue
            line = f"{role_labels.get(message.role, message.role)}: {content}"
            if total_chars + len(line) + 1 > self.MAX_CONTEXT_HISTORY_CHARS:
                break
            lines.append(line)
            total_chars += len(line) + 1

        if len(lines) == 1:
            return []
        return ["\n".join(lines)]

    def _truncate_history_message(self, content: str) -> str:
        if len(content) <= self.MAX_CONTEXT_HISTORY_MESSAGE_CHARS:
            return content
        return content[: self.MAX_CONTEXT_HISTORY_MESSAGE_CHARS - 3].rstrip() + "..."

    def _resolve_lms_scope(
        self,
        db: Session,
        course_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
    ) -> LMSChatScope:
        # Xác định phạm vi khóa học/buổi học và tình trạng tài liệu RAG.
        """Resolve course/lesson names and RAG document availability."""
        course: Course | None = None
        lesson: Lesson | None = None

        if lesson_id:
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if not lesson:
                raise ValueError("Lesson not found.")
            if course_id and lesson.course_id != course_id:
                raise ValueError("Lesson does not belong to the requested course.")
            course = lesson.course
            course_id = lesson.course_id
        elif course_id:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                raise ValueError("Course not found.")

        has_lesson_rag_documents = False
        if lesson_id:
            has_lesson_rag_documents = (
                db.query(RAGDocument)
                .filter(
                    RAGDocument.lesson_id == lesson_id,
                    RAGDocument.is_active == 1,
                )
                .count()
                > 0
            )

        has_course_rag_documents = False
        if course_id:
            has_course_rag_documents = (
                db.query(RAGDocument)
                .filter(
                    RAGDocument.course_id == course_id,
                    RAGDocument.lesson_id.is_(None),
                    RAGDocument.is_active == 1,
                )
                .count()
                > 0
            )

        return LMSChatScope(
            course_id=course_id,
            course_title=course.title if course else None,
            course_level=course.level if course else None,
            lesson_id=lesson_id,
            lesson_title=lesson.title if lesson else None,
            has_lesson_rag_documents=has_lesson_rag_documents,
            has_course_rag_documents=has_course_rag_documents,
        )

    def _build_auto_rag_context(
        self,
        db: Session,
        question: str,
        scope: LMSChatScope,
    ) -> list[str]:
        # Lấy ngữ cảnh RAG tự động theo ưu tiên buổi học trước, khóa học sau.
        """Retrieve classroom RAG context with lesson-first priority."""
        _ = db
        if not scope.course_id and not scope.lesson_id:
            return []

        rag_service = self._get_rag_service()
        contexts: list[str] = []
        seen_chunks: set[str] = set()

        if scope.lesson_id and scope.has_lesson_rag_documents:
            lesson_result = rag_service.search(
                query=question,
                top_k=4,
                course_id=str(scope.course_id) if scope.course_id else None,
                lesson_id=str(scope.lesson_id),
            )
            contexts.extend(
                self._format_rag_results(
                    label="PRIMARY_LESSON_CONTEXT",
                    results=lesson_result.get("results", []),
                    seen_chunks=seen_chunks,
                )
            )

        if scope.course_id and scope.has_course_rag_documents:
            course_result = rag_service.search(
                query=question,
                top_k=2 if scope.has_lesson_rag_documents else 5,
                course_id=str(scope.course_id),
                course_only=True,
            )
            contexts.extend(
                self._format_rag_results(
                    label=(
                        "SUPPORTING_COURSE_CONTEXT"
                        if scope.has_lesson_rag_documents
                        else "PRIMARY_COURSE_CONTEXT"
                    ),
                    results=course_result.get("results", []),
                    seen_chunks=seen_chunks,
                )
            )

        return contexts

    def _get_rag_service(self) -> Any:
        if self.rag_service is not None:
            return self.rag_service

        from llm.rag.service import get_rag_service

        self.rag_service = get_rag_service(
            use_postgres=True,
            verbose=False,
            initialize_schema=False,
        )
        return self.rag_service

    def _format_rag_results(
        self,
        label: str,
        results: Sequence[dict[str, Any]],
        seen_chunks: set[str],
    ) -> list[str]:
        formatted: list[str] = []
        for index, result in enumerate(results, start=1):
            chunk_id = str(result.get("chunk_id") or "")
            if chunk_id and chunk_id in seen_chunks:
                continue
            if chunk_id:
                seen_chunks.add(chunk_id)

            source = (
                result.get("document_title")
                or result.get("document_id")
                or result.get("doc_id")
                or "LMS material"
            )
            page_number = result.get("page_number")
            relevance = result.get("relevance")
            content = (result.get("content") or "").strip()
            if not content:
                continue

            meta_parts = [f"Source: {source}"]
            if page_number:
                meta_parts.append(f"page {page_number}")
            if isinstance(relevance, (float, int)):
                meta_parts.append(f"relevance {float(relevance):.3f}")

            formatted.append(
                f"[{label} #{index}]\n"
                f"{'; '.join(meta_parts)}\n"
                f"{content}"
            )

        return formatted

    def _get_or_create_conversation(
        self,
        db: Session,
        user_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
        conversation_title: str | None,
        course_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
        reuse_existing: bool = True,
    ) -> AIConversation:
        if conversation_id:
            conversation = (
                db.query(AIConversation)
                .filter(
                    AIConversation.id == conversation_id,
                    AIConversation.user_id == user_id,
                )
                .first()
            )
            if not conversation:
                raise ValueError("Conversation not found.")
            if conversation_title:
                conversation.title = conversation_title[:255]
            return conversation

        query = db.query(AIConversation).filter(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,
        )

        if course_id is None:
            query = query.filter(AIConversation.course_id.is_(None))
        else:
            query = query.filter(AIConversation.course_id == course_id)

        if lesson_id is None:
            query = query.filter(AIConversation.lesson_id.is_(None))
        else:
            query = query.filter(AIConversation.lesson_id == lesson_id)

        conversation = query.order_by(desc(AIConversation.updated_at)).first()
        if conversation and reuse_existing:
            if conversation_title:
                conversation.title = conversation_title[:255]
            return conversation

        title_seed = (conversation_title or question).strip()
        conversation = AIConversation(
            user_id=user_id,
            course_id=course_id,
            lesson_id=lesson_id,
            title=title_seed[:255] if title_seed else "Chat with AI Tutor",
            is_active=True,
        )
        db.add(conversation)
        db.flush()
        return conversation

    def _prepare_teaching_images(
        self,
        teaching_images: Sequence[dict[str, str | None]],
    ) -> tuple[list[ImageInput], list[str]]:
        # Giải mã/kiểm tra ảnh từ client và tạo metadata để đưa vào prompt.
        prepared_images: list[ImageInput] = []
        derived_contexts: list[str] = []

        for index, raw_image in enumerate(teaching_images, start=1):
            mime_type = (raw_image.get("mime_type") or "").strip().lower()
            if mime_type not in self.ALLOWED_IMAGE_MIME_TYPES:
                raise ValueError(
                    "Unsupported image mime type. "
                    f"Allowed types: {sorted(self.ALLOWED_IMAGE_MIME_TYPES)}"
                )

            data_base64 = (raw_image.get("data_base64") or "").strip()
            if data_base64.startswith("data:"):
                header, separator, encoded_data = data_base64.partition(",")
                if not separator:
                    raise ValueError(
                        f"teaching_images[{index - 1}] has invalid data URL format."
                    )
                mime_from_data_url = header[5:].split(";", 1)[0].strip().lower()
                if mime_from_data_url and mime_from_data_url != mime_type:
                    raise ValueError(
                        "Image mime_type does not match data URL mime type."
                    )
                data_base64 = encoded_data

            # Some clients insert line breaks/spaces in base64 payloads.
            data_base64 = "".join(data_base64.split())
            try:
                image_data = base64.b64decode(data_base64, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError(
                    f"teaching_images[{index - 1}] has invalid base64 data."
                ) from exc

            if not image_data:
                raise ValueError(f"teaching_images[{index - 1}] is empty.")

            if len(image_data) > self.MAX_IMAGE_BYTES:
                raise ValueError(
                    "Image is too large. Maximum allowed size is 10MB per image."
                )

            description = (raw_image.get("description") or "").strip() or None
            source = (raw_image.get("source") or "screen_capture").strip() or "screen_capture"

            prepared_images.append(
                ImageInput(
                    data=image_data,
                    mime_type=mime_type,
                    description=description,
                    source=source,
                )
            )

            image_size_kb = len(image_data) / 1024
            if description:
                derived_contexts.append(
                    f"{source} #{index} ({mime_type}, {image_size_kb:.1f}KB): {description}"
                )
            else:
                derived_contexts.append(
                    f"{source} #{index} ({mime_type}, {image_size_kb:.1f}KB)"
                )

        return prepared_images, derived_contexts


def _format_image_context_message(image_contexts: Sequence[str]) -> str:
    lines = ["Image contexts for this turn:"]
    lines.extend(f"- {item}" for item in image_contexts)
    return "\n".join(lines)


def _merge_optional_text(primary: str | None, secondary: str | None) -> str | None:
    parts = [part.strip() for part in [primary, secondary] if part and part.strip()]
    if not parts:
        return None
    return "\n\n".join(parts)


def _need_teaching_image_strict(text: str) -> bool:
    normalized = text.lower().strip()
    if not normalized:
        return False

    deictic_strong = [
        "anh nay",
        "ảnh này",
        "tam anh nay",
        "tấm ảnh này",
        "buc anh nay",
        "bức ảnh này",
        "hinh anh nay",
        "hình ảnh này",

        "slide nay",
        "slide này",

        "video nay",
        "video này",
        "clip nay",
        "clip này",
        "doan video nay",
        "đoạn video này",
        "doan clip nay",
        "đoạn clip này",

        "man hinh nay",
        "màn hình này",
        "anh chup man hinh nay",
        "ảnh chụp màn hình này",
    ]

    visual_context = [
        "trong anh",
        "trong ảnh",
        "tren anh",
        "trên ảnh",

        "trong buc anh",
        "trong bức ảnh",
        "tren buc anh",
        "trên bức ảnh",

        "trong tam anh",
        "trong tấm ảnh",
        "tren tam anh",
        "trên tấm ảnh",

        "trong clip",
        "tren clip",
        "trên clip",

        "trong video",
        "trên video",
        "tren video",

        "trong doan video",
        "trong đoạn video",
        "tren doan video",
        "trên đoạn video",

        "trong clip",
        "tren clip",
        "trên clip",

        "trong doan clip",
        "trong đoạn clip",
        "tren doan clip",
        "trên đoạn clip",

        "trong screenshot",
        "tren screenshot",
        "trên screenshot",

        "trong anh chup man hinh",
        "trong ảnh chụp màn hình",
        "tren anh chup man hinh",
        "trên ảnh chụp màn hình",

        "trong man hinh",
        "trong màn hình",
        "tren man hinh",
        "trên màn hình",

        "trong slide",
        "tren slide",
        "trên slide",

        "trong khung hinh",
        "trong khung hình",
        "tren khung hinh",
        "trên khung hình",

        "trong frame",
        "tren frame",
        "trên frame",
    ]

    visual_action = [
        "xem hinh",
        "xem hình",
        "xem anh",
        "xem ảnh",
        "xem video",
        "xem clip",
        "xem slide",
        "xem man hinh",
        "xem màn hình",

        "nhin hinh",
        "nhìn hình",
        "nhin anh",
        "nhìn ảnh",
        "nhin video",
        "nhìn video",
        "nhin slide",
        "nhìn slide",
        "nhin man hinh",
        "nhìn màn hình",

        "dua vao hinh",
        "dựa vào hình",
        "dua vao anh",
        "dựa vào ảnh",
        "dua vao video",
        "dựa vào video",
        "dua vao slide",
        "dựa vào slide",

        "giai thich hinh nay",
        "giải thích hình này",
        "giai thich anh nay",
        "giải thích ảnh này",
        "giai thich video nay",
        "giải thích video này",
        "giai thich slide nay",
        "giải thích slide này",

        "phan tich hinh nay",
        "phân tích hình này",
        "phan tich anh nay",
        "phân tích ảnh này",
        "phan tich video nay",
        "phân tích video này",
        "phan tich slide nay",
        "phân tích slide này",

        "mo ta hinh nay",
        "mô tả hình này",
        "mo ta anh nay",
        "mô tả ảnh này",
        "mo ta video nay",
        "mô tả video này",

        "doc hinh nay",
        "đọc hình này",
        "doc anh nay",
        "đọc ảnh này",
        "doc bieu do nay",
        "đọc biểu đồ này",
        "doc bang nay",
        "đọc bảng này",
        "doc so do nay",
        "đọc sơ đồ này",

        "ve lai hinh nay",
        "vẽ lại hình này",
        "ve lai anh nay",
        "vẽ lại ảnh này",
        "ve lai so do nay",
        "vẽ lại sơ đồ này",
    ]

    if any(keyword in normalized for keyword in deictic_strong):
        return True

    if any(keyword in normalized for keyword in visual_context):
        return True

    if any(keyword in normalized for keyword in visual_action):
        return True

    return (
        re.search(r"đang\s+.*\s+gì", normalized) is not None
        or re.search(r"dang\s+.*\s+gi", normalized) is not None
    )
