"""Prompt helpers for chatbot workflows."""


def default_chatbot_prompt() -> str:
    """Default system prompt for the chatbot assistant."""
    return (
        "You are an AI teaching assistant in an LMS. Answer briefly, accurately, "
        "and directly. Ground your answer in the provided context when available. "
        "When the context is incomplete, use the course title, lesson title, and "
        "your subject-matter knowledge to infer the most helpful response."
    )


def build_lms_chatbot_prompt(
    course_title: str | None = None,
    lesson_title: str | None = None,
) -> str:
    """Build the LMS classroom system prompt with course/lesson metadata."""
    course_name = (course_title or "Chưa xác định").strip()
    lesson_name = (lesson_title or "Chưa xác định").strip()
    return "\n".join(
        [
            default_chatbot_prompt(),
            "",
            f"Course: {course_name}",
            f"Lesson or classroom: {lesson_name}",
            "",
            "Role: act as a tutor for this subject or course.",
            "Prefer PRIMARY_LESSON_CONTEXT when it is present; use SUPPORTING_COURSE_CONTEXT to supplement or verify.",
            "Use CONVERSATION_HISTORY_CONTEXT for continuity, but prioritize the current image or RAG context for the latest answer.",
            "If the context is not sufficient for a final conclusion, do not apologize, do not say the system lacks context, and do not blame the platform.",
            "Instead, use subject-matter knowledge and reasonable inference from the course and lesson names to answer the most useful part of the question.",
            "If you must infer, keep the answer short and useful; you may briefly note that the answer is based on subject knowledge when the LMS materials do not fully cover it.",
            "Respond in Vietnamese. Stay concise unless the learner asks for more detail.",
        ]
    )
