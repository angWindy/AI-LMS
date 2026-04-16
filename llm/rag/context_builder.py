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
    ) -> ContextTrace:
        """Return context trace containing merged context and inputs."""


class DefaultContextBuilder:
    """Builds a merged context block for RAG and image metadata."""

    def build_context(
        self,
        question: str,
        rag_context: Sequence[str] | None,
        image_contexts: Sequence[str] | None,
    ) -> ContextTrace:
        _ = question
        rag_context_list = list(rag_context or [])
        image_contexts_list = list(image_contexts or [])
        merged_context = _merge_context_blocks(rag_context_list, image_contexts_list)
        return ContextTrace(
            rag_context=rag_context_list,
            image_contexts=image_contexts_list,
            merged_context=merged_context,
        )


def _merge_context_blocks(
    rag_context: Sequence[str],
    image_contexts: Sequence[str],
) -> str | None:
    sections: list[str] = []
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
