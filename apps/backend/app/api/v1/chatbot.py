"""Chatbot API endpoints."""
from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.dependencies import CurrentUser
from app.schemas.chatbot import (
    ChatbotAskRequest,
    ChatbotAskResponse,
    ChatMessagePayload,
    ContextTracePayload,
)
from app.services.chatbot_service import ChatbotService
from llm.models import ChatMessage

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


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
async def ask_chatbot(
    payload: ChatbotAskRequest,
    current_user: CurrentUser,
) -> ChatbotAskResponse:
    """Generate an assistant response for a learner/instructor question."""
    _ = current_user
    service = ChatbotService()
    history = [
        ChatMessage(role=message.role, content=message.content)
        for message in payload.history
    ]

    try:
        response = service.ask(
            question=payload.question,
            history=history,
            system_prompt=payload.system_prompt,
            context_docs=payload.context_docs,
            image_contexts=payload.image_contexts,
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

    return ChatbotAskResponse(
        answer=response.answer,
        provider=response.provider,
        model=response.model,
        finish_reason=response.finish_reason,
        usage=response.usage,
        messages=[
            ChatMessagePayload(role=message.role, content=message.content)
            for message in response.messages
        ],
        context=ContextTracePayload(
            rag_context=response.context.rag_context,
            image_contexts=response.context.image_contexts,
            merged_context=response.context.merged_context,
        ),
    )