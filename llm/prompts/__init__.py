"""Prompt templates used by LLM workflows."""

from llm.prompts.assignment_generator import build_assignment_generator_prompt
from llm.prompts.assignment_chatbot import build_assignment_tutor_prompt
from llm.prompts.chatbot import build_lms_chatbot_prompt, default_chatbot_prompt
from llm.prompts.learning_level import (
    build_learning_level_prompt_block,
    learning_level_guidance,
    learning_level_label,
    normalize_learning_level,
)

__all__ = [
    "build_lms_chatbot_prompt",
    "default_chatbot_prompt",
    "build_assignment_generator_prompt",
    "build_assignment_tutor_prompt",
    "build_learning_level_prompt_block",
    "learning_level_guidance",
    "learning_level_label",
    "normalize_learning_level",
]
