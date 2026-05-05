"""Prompt templates used by LLM workflows."""

from llm.prompts.assignment_generator import build_assignment_generator_prompt
from llm.prompts.assignment_chatbot import build_assignment_tutor_prompt
from llm.prompts.chatbot import build_lms_chatbot_prompt, default_chatbot_prompt

__all__ = [
    "build_lms_chatbot_prompt",
    "default_chatbot_prompt",
    "build_assignment_generator_prompt",
    "build_assignment_tutor_prompt",
]
