"""Chatbot orchestration service with future-ready extension points."""
from collections.abc import Sequence

from app.core.config import settings
from llm.config import LLMConfig
from llm.models import ChatMessage
from llm.rag.context_builder import ContextBuilder, DefaultContextBuilder
from llm.workflows.chatbot import ChatbotResult, ChatbotWorkflow


class ChatbotService:
    """Coordinates prompt assembly and delegates text generation to a provider."""

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
        question: str,
        history: Sequence[ChatMessage] | None = None,
        system_prompt: str | None = None,
        context_docs: Sequence[str] | None = None,
        image_contexts: Sequence[str] | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        thinking_level: str | None = None,
    ) -> ChatbotResult:
        """Generate one assistant answer for the provided question."""
        return self.workflow.run(
            question=question,
            history=history,
            system_prompt=system_prompt,
            rag_context=context_docs,
            image_contexts=image_contexts,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            thinking_level=thinking_level,
        )