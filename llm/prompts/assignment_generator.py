"""Prompt helpers for assignment generation workflows."""


DIFFICULTY_LEVELS = {
    "easy": """
- Tests basic knowledge and recall.
- Focuses on concepts, definitions, or directly stated facts.
- Requires little to no reasoning.
- Question length should be short and direct, usually 1 sentence.
- Avoid unnecessary context or long scenarios.
""",
    "medium": """
- Tests understanding and application.
- May require comparison, explanation, or short reasoning.
- Cannot be answered by recall alone.
- Question length should be moderate, usually 1-2 sentences.
- May include a simple scenario, short example, or small code snippet if relevant.
""",
    "hard": """
- Tests analysis and deeper reasoning.
- Requires combining multiple concepts or solving a problem.
- Distractors must be plausible and difficult to distinguish.
- Question length should be long enough to fully present the problem, context, code, data, or scenario.
- Hard questions may contain 2-4 sentences, a realistic situation, or a concise code snippet.
- Do not shorten hard questions in a way that removes necessary reasoning context.
- The length should support complexity, not add unnecessary verbosity.
"""
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
15. Adapt every question, option, distractor, example, and explanation implied by the answer key to the learner level stated in Course context.
16. Keep the academic target correct; learner level changes wording, scaffolding, context familiarity, and reasoning depth, not factual correctness.

Question length and complexity rules:
17. The length and structure of each question must match its difficulty.
18. Easy questions should be short, direct, and focused on one basic concept.
19. Medium questions should be moderately detailed and may include a small scenario, example, comparison, or short reasoning requirement.
20. Hard questions must be long enough to include all necessary context, constraints, code snippets, data, or scenario details required for deeper reasoning.
21. Do not make hard questions overly short if doing so makes the question become theoretical, ambiguous, or answerable by memorization.
22. Do not add filler text only to make a question longer. Length must serve the reasoning requirement.
23. For programming or practical subjects, medium and hard questions should often include code snippets, debugging situations, design scenarios, or output prediction tasks.
24. If a hard question includes code, keep the code concise but complete enough for the learner to reason correctly.
25. If code is included inside JSON strings, escape newline characters and quotation marks properly so the final output remains valid JSON.

Practice-oriented question rules:
26. If the lesson is practice-oriented, especially programming, algorithms, databases, web development, software engineering, or other technical/practical subjects, the question set must include practical application questions, not only theoretical recall.
27. For practice-oriented lessons, at least 60% of the questions must be application-based.
28. Application-based questions may include:
    - reading a short code snippet and predicting the output;
    - identifying an error or bug in code;
    - choosing the best implementation;
    - selecting the correct class, method, attribute, access modifier, or design relationship;
    - applying a concept to a realistic programming scenario;
    - comparing alternative solutions and choosing the most appropriate one.
29. For object-oriented programming lessons, prioritize practical questions about objects, classes, constructors, encapsulation, inheritance, polymorphism, overriding, overloading, access modifiers, composition, interfaces, abstract classes, and class relationships when relevant to the lesson.
30. Hard questions in practical subjects should require reasoning through code behavior, object interaction, design choice, or subtle conceptual differences, not simple memorization.
Course context:
{course_context}

Lesson context:
{lesson_context}
""".strip()
