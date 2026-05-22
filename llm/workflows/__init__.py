"""Workflow implementations for LLM tasks."""

from llm.workflows.assignment_generator import (
    AssignmentGeneratorResult,
    AssignmentGeneratorWorkflow,
)
from llm.workflows.chatbot import ChatbotResult, ChatbotWorkflow

__all__ = [
    "ChatbotResult",
    "ChatbotWorkflow",
    "AssignmentGeneratorResult",
    "AssignmentGeneratorWorkflow",
]
