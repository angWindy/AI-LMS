"""Builds context blocks for retrieval-augmented generation."""
from collections.abc import Sequence
from typing import Protocol

from llm.models import ContextTrace


class ContextBuilder(Protocol):
    """Interface for building context blocks before LLM generation."""

    def build_context(
        self,
        question: str,
        rag_context: Sequence[str] | None,
        image_contexts: Sequence[str] | None,
        conversation_history: Sequence[str] | None = None,
    ) -> ContextTrace:
        """Return context trace containing merged context and inputs."""


class DefaultContextBuilder:
    """Builds a merged context block for RAG and image metadata."""

    def build_context(
        self,
        question: str,
        rag_context: Sequence[str] | None,
        image_contexts: Sequence[str] | None,
        conversation_history: Sequence[str] | None = None,
    ) -> ContextTrace:
        _ = question
        rag_context_list = list(rag_context or [])
        image_contexts_list = list(image_contexts or [])
        conversation_history_list = list(conversation_history or [])
        merged_context = _merge_context_blocks(
            conversation_history_list,
            rag_context_list,
            image_contexts_list,
        )
        return ContextTrace(
            rag_context=rag_context_list,
            image_contexts=image_contexts_list,
            conversation_history=conversation_history_list,
            merged_context=merged_context,
        )


def _merge_context_blocks(
    conversation_history: Sequence[str],
    rag_context: Sequence[str],
    image_contexts: Sequence[str],
) -> str | None:
    sections: list[str] = []
    if conversation_history:
        sections.append(
            "CONVERSATION_HISTORY_CONTEXT:\n"
            + "\n".join(f"- {item}" for item in conversation_history)
        )
    if image_contexts:
        sections.append(
            "IMAGE_CONTEXT:\n" + "\n".join(f"- {item}" for item in image_contexts)
        )
    if rag_context:
        sections.append(
            "RAG_CONTEXT:\n" + "\n".join(f"- {item}" for item in rag_context)
        )
    if not sections:
        return None
    return "\n\n".join(sections)
