"""Prompt helpers for chatbot workflows."""


def default_chatbot_prompt() -> str:
    """Default system prompt for the chatbot assistant."""
    return (
        "You are a helpful learning assistant. Keep answers concise, "
        "accurate, and aligned with the provided context."
    )
