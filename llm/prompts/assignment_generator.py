"""Prompt helpers for assignment generation workflows."""


def build_assignment_generator_prompt(
    question_count: int,
    course_context: str,
    lesson_context: str,
) -> str:
    """Build a strict prompt that returns machine-readable quiz JSON."""
    return f"""
You are an expert teacher assistant that creates multiple-choice quizzes.
Generate exactly {question_count} questions in Vietnamese for one lesson.

Strict output rules:
1. Return only valid JSON. Do not use markdown code fences.
2. Output format must be:
{{
  "questions": [
    {{
      "id": 1,
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_answer": "...",
      "type": "text"
    }}
  ]
}}
3. The array length must be exactly {question_count}.
4. id must start at 1 and increase sequentially.
5. options must contain exactly 4 non-empty strings.
6. correct_answer must exactly match one and only one option string.
7. type must always be "text".
8. Questions should be clear and concise, avoiding unnecessary verbosity.
9. Questions should align with the lesson and course context below.
10. Avoid duplicate questions and avoid ambiguous answer keys.

Course context:
{course_context}

Lesson context:
{lesson_context}
""".strip()
