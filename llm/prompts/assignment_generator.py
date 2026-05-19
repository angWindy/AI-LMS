"""Prompt helpers for assignment generation workflows."""


DIFFICULTY_LEVELS = {
    "easy": """
- Tests basic knowledge and recall.
- Focuses on concepts, definitions, or directly stated facts.
- Requires little to no reasoning.
""",
    "medium": """
- Tests understanding and application.
- May require comparison, explanation, or short reasoning.
- Cannot be answered by recall alone.
""",
    "hard": """
- Tests analysis and deeper reasoning.
- Requires combining multiple concepts or solving a problem.
- Distractors must be plausible and difficult to distinguish.
""",
}


def calculate_ratio_counts(total: int, ratios: dict[str, float]) -> dict[str, int]:
    """Allocate an integer total by ratio using largest remainders."""
    raw_counts = {key: total * ratio for key, ratio in ratios.items()}
    counts = {key: int(value) for key, value in raw_counts.items()}
    remaining = total - sum(counts.values())

    sorted_keys = sorted(
        ratios,
        key=lambda key: (raw_counts[key] - counts[key], ratios[key]),
        reverse=True,
    )
    for key in sorted_keys[:remaining]:
        counts[key] += 1

    return counts


def difficulty_distribution(question_count: int) -> dict[str, int]:
    """Return the 40/40/20 easy/medium/hard distribution for a question set."""
    return calculate_ratio_counts(
        question_count,
        {
            "easy": 0.4,
            "medium": 0.4,
            "hard": 0.2,
        },
    )


def _format_difficulty_levels() -> str:
    labels = {
        "easy": "Easy",
        "medium": "Medium",
        "hard": "Hard",
    }
    return "\n\n".join(
        f'{key} ({labels[key]}):\n{description.strip()}'
        for key, description in DIFFICULTY_LEVELS.items()
    )


def build_assignment_generator_prompt(
    question_count: int,
    course_context: str,
    lesson_context: str,
) -> str:
    """Build a strict prompt that returns machine-readable quiz JSON."""
    counts = difficulty_distribution(question_count)
    difficulty_counts = ", ".join(
        f'{count} "{difficulty}"'
        for difficulty, count in counts.items()
    )
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
      "difficulty": "...",
      "type": "text"
    }}
  ]
}}
3. The array length must be exactly {question_count}.
4. id must start at 1 and increase sequentially.
5. options must contain exactly 4 non-empty strings.
6. correct_answer must exactly match one and only one option string.
7. difficulty must be exactly one of: "easy", "medium", "hard".
8. type must always be "text".
9. The question set must contain exactly this difficulty distribution: {difficulty_counts}.
10. Use these difficulty definitions:
{_format_difficulty_levels()}
11. Questions should be clear and concise, avoiding unnecessary verbosity.
12. Questions should align with the lesson and course context below.
13. Avoid duplicate questions and avoid ambiguous answer keys.
14. For hard questions, make distractors plausible and difficult to distinguish.

Course context:
{course_context}

Lesson context:
{lesson_context}
""".strip()
