"""Chatbot orchestration service with future-ready extension points."""
import base64
import binascii
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_interaction import AIConversation, AIMessage
from llm.config import LLMConfig
from llm.models import ChatMessage, ImageInput
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


class ChatbotService:
    """Coordinates prompt assembly and delegates text generation to a provider."""

    MAX_CONVERSATION_HISTORY_MESSAGES = 40
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
    ) -> ChatbotServiceResult:
        """Generate one assistant answer and persist the turn into conversation history."""
        conversation = self._get_or_create_conversation(
            db=db,
            user_id=user_id,
            question=question,
            conversation_id=conversation_id,
            conversation_title=conversation_title,
            course_id=course_id,
            lesson_id=lesson_id,
        )

        persisted_history = self._load_conversation_history(db, conversation.id)
        runtime_history = list(persisted_history)
        if not conversation_id and history:
            runtime_history.extend(history)

        incoming_teaching_images = list(teaching_images or [])
        image_rule_matched = _need_teaching_image_strict(question)
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

        llm_result = self.workflow.run(
            question=question,
            history=runtime_history,
            system_prompt=system_prompt,
            rag_context=context_docs,
            image_contexts=merged_image_contexts,
            images=prepared_images,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )

        logger.debug(
            "[Debug] Chatbot service assembled request provider=%s model=%s user_id=%s conversation_id=%s image_rule_matched=%s has_image_input=%s image_input_count=%s image_used_count=%s rag_context_count=%s merged_image_context_count=%s",
            llm_result.provider,
            llm_result.model,
            user_id,
            conversation.id,
            image_rule_matched,
            len(incoming_teaching_images) > 0,
            len(incoming_teaching_images),
            len(prepared_images),
            len(context_docs or []),
            len(merged_image_contexts),
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

    def _get_or_create_conversation(
        self,
        db: Session,
        user_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
        conversation_title: str | None,
        course_id: uuid.UUID | None,
        lesson_id: uuid.UUID | None,
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
        if conversation:
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


def _need_teaching_image_strict(text: str) -> bool:
    normalized = text.lower().strip()
    if not normalized:
        return False

    deictic_strong = [
        "cai nay",
        "cái này",
        "doan nay",
        "đoạn này",
        "cho nay",
        "chỗ này",
        "slide nay",
        "slide này",
        "dong nay",
        "dòng này",
        "frame nay",
        "frame này",
    ]

    visual_context = [
        "trong video",
        "tren man hinh",
        "trên màn hình",
        "trong slide",
        "tren hinh",
        "trên hình",
        "trong hinh",
        "trong hình",
    ]

    visual_action = [
        "ve cai",
        "vẽ cái",
        "ve lai",
        "vẽ lại",
        "plot cai",
        "plot cái",
        "minh hoa cai",
        "minh họa cái",
        "draw this",
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