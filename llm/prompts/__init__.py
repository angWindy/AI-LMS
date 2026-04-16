"""Prompt templates used by LLM workflows."""

from llm.prompts.assignment_generator import build_assignment_generator_prompt
from llm.prompts.chatbot import default_chatbot_prompt

__all__ = ["default_chatbot_prompt", "build_assignment_generator_prompt"]
