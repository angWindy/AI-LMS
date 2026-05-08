"""Workflow implementations for LLM tasks."""

from llm.workflows.assignment_generator import (
    AssignmentGeneratorResult,
    AssignmentGeneratorWorkflow,
)
from llm.workflows.chatbot import ChatbotResult, ChatbotWorkflow
from llm.workflows.slide_generator import (
    SlideGeneratorResult,
    SlideGeneratorWorkflow,
    generate_document_ir,
    generate_slides_from_context,
    generate_slides_from_ir,
)

__all__ = [
    "ChatbotResult",
    "ChatbotWorkflow",
    "AssignmentGeneratorResult",
    "AssignmentGeneratorWorkflow",
    "SlideGeneratorResult",
    "SlideGeneratorWorkflow",
    "generate_document_ir",
    "generate_slides_from_ir",
    "generate_slides_from_context",
]
