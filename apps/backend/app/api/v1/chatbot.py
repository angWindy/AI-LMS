"""Chatbot API endpoints."""
import logging
import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.dependencies import CurrentUser, DBSession
from app.schemas.chatbot import (
    AssignmentChatbotAskRequest,
    AssignmentChatbotPreloadRequest,
    AssignmentChatbotPreloadResponse,
    ChatbotAskRequest,
    ChatbotAskResponse,
    ChatMessagePayload,
    ConversationMessagePayload,
    ConversationMessagesResponse,
    ConversationSummaryPayload,
    ContextTracePayload,
)
from app.services.assignment_chatbot_service import AssignmentChatbotService
from app.services.chatbot_service import ChatbotService
from llm.models import ChatMessage

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])
logger = logging.getLogger(__name__)


@router.get("/providers")
async def list_chatbot_providers(current_user: CurrentUser) -> dict:
    """Return active provider and baseline available providers."""
    _ = current_user
    return {
        "active_provider": settings.LLM_PROVIDER,
        "active_model": settings.LLM_MODEL,
        "supported_providers": ["google", "mock"],
    }


@router.post("/ask", response_model=ChatbotAskResponse)
def ask_chatbot(
    db: DBSession,
    payload: ChatbotAskRequest,
    current_user: CurrentUser,
) -> ChatbotAskResponse:
    """Generate an assistant response for a learner/instructor question."""
    service = ChatbotService()
    history = [
        ChatMessage(role=message.role, content=message.content)
        for message in payload.history
    ]
    teaching_images = [image.model_dump() for image in payload.teaching_images]

    try:
        response = service.ask(
            db=db,
            user_id=current_user.id,
            question=payload.question,
            history=history,
            system_prompt=payload.system_prompt,
            conversation_id=payload.conversation_id,
            conversation_title=payload.conversation_title,
            course_id=payload.course_id,
            lesson_id=payload.lesson_id,
            context_docs=payload.context_docs,
            image_contexts=payload.image_contexts,
            teaching_images=teaching_images,
            temperature=payload.temperature,
            max_output_tokens=payload.max_output_tokens,
            thinking_level=payload.thinking_level,
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

    question_preview = payload.question.strip().replace("\n", " ")
    if len(question_preview) > 120:
        question_preview = f"{question_preview[:120]}..."
    image_rule_matched = response.image_rule_matched
    image_input_count = response.image_input_count
    has_image_input = image_input_count > 0
    image_used_count = response.image_used_count
    has_image_used = image_used_count > 0
    context_count = len(payload.context_docs or []) + len(payload.image_contexts or [])

    logger.info(
        "[Success] Chatbot ask succeeded user=%s conversation_id=%s provider=%s model=%s image_rule_matched=%s has_image_input=%s image_input_count=%s has_image_used=%s image_used_count=%s context_count=%s question=%s",
        current_user.email,
        response.conversation_id,
        response.result.provider,
        response.result.model,
        image_rule_matched,
        has_image_input,
        image_input_count,
        has_image_used,
        image_used_count,
        context_count,
        question_preview,
    )

    return ChatbotAskResponse(
        answer=response.result.answer,
        conversation_id=response.conversation_id,
        conversation_title=response.conversation_title,
        provider=response.result.provider,
        model=response.result.model,
        finish_reason=response.result.finish_reason,
        usage=response.result.usage,
        messages=[
            ChatMessagePayload(role=message.role, content=message.content)
            for message in response.result.messages
        ],
        context=ContextTracePayload(
            rag_context=response.result.context.rag_context,
            image_contexts=response.result.context.image_contexts,
            merged_context=response.result.context.merged_context,
        ),
    )


@router.post("/assignment/preload", response_model=AssignmentChatbotPreloadResponse)
def preload_assignment_chatbot(
    db: DBSession,
    payload: AssignmentChatbotPreloadRequest,
    current_user: CurrentUser,
) -> AssignmentChatbotPreloadResponse:
    """Warm sanitized assignment context for the assignment support chatbot."""
    service = AssignmentChatbotService()
    try:
        preload_result = service.preload_context(
            db=db,
            user=current_user,
            assignment_id=payload.assignment_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    logger.info(
        "[Success] Assignment chatbot context preloaded user=%s assignment_id=%s question_count=%s context_length=%s",
        current_user.email,
        preload_result["assignment_id"],
        preload_result["question_count"],
        preload_result["context_length"],
    )

    return AssignmentChatbotPreloadResponse(**preload_result)


@router.post("/assignment/ask", response_model=ChatbotAskResponse)
def ask_assignment_chatbot(
    db: DBSession,
    payload: AssignmentChatbotAskRequest,
    current_user: CurrentUser,
) -> ChatbotAskResponse:
    """Generate a guided hint for a learner working on an assignment."""
    service = AssignmentChatbotService()
    history = [
        ChatMessage(role=message.role, content=message.content)
        for message in payload.history
    ]

    try:
        response = service.ask(
            db=db,
            user=current_user,
            assignment_id=payload.assignment_id,
            question=payload.question,
            history=history,
            conversation_id=payload.conversation_id,
            temperature=payload.temperature,
            max_output_tokens=payload.max_output_tokens,
            thinking_level=payload.thinking_level,
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

    logger.info(
        "[Success] Assignment chatbot ask succeeded user=%s assignment_id=%s conversation_id=%s provider=%s model=%s question=%s",
        current_user.email,
        payload.assignment_id,
        response.conversation_id,
        response.result.provider,
        response.result.model,
        payload.question.strip().replace("\n", " ")[:120],
    )

    return ChatbotAskResponse(
        answer=response.result.answer,
        conversation_id=response.conversation_id,
        conversation_title=response.conversation_title,
        provider=response.result.provider,
        model=response.result.model,
        finish_reason=response.result.finish_reason,
        usage=response.result.usage,
        messages=[
            ChatMessagePayload(role=message.role, content=message.content)
            for message in response.result.messages
        ],
        context=ContextTracePayload(
            rag_context=response.result.context.rag_context,
            image_contexts=response.result.context.image_contexts,
            merged_context=response.result.context.merged_context,
        ),
    )


@router.get("/conversations", response_model=list[ConversationSummaryPayload])
async def list_conversations(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = 20,
) -> list[ConversationSummaryPayload]:
    """List recent chatbot conversations for the current user."""
    service = ChatbotService()
    conversations = service.list_conversations(
        db=db,
        user_id=current_user.id,
        limit=max(1, min(limit, 100)),
    )
    return [
        ConversationSummaryPayload(
            id=conversation.id,
            title=conversation.title,
            course_id=conversation.course_id,
            lesson_id=conversation.lesson_id,
            is_active=conversation.is_active,
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
async def list_conversation_messages(
    db: DBSession,
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    limit: int = 100,
) -> ConversationMessagesResponse:
    """List messages of one chatbot conversation belonging to current user."""
    service = ChatbotService()
    try:
        messages = service.list_messages(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation_id,
            limit=max(1, min(limit, 500)),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[
            ConversationMessagePayload(
                id=message.id,
                role=message.role,
                content=message.content,
                model_version=message.model_version,
                tokens_used=message.tokens_used,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )
