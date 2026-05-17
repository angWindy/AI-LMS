"""Prompt helpers for assignment feedback workflows."""


def build_assignment_feedback_prompt(
    course_context: str,
    scope_context: str,
    submission_context: str,
) -> str:
    """Build a strict JSON prompt for post-submission feedback."""
    return f"""
You are an expert Vietnamese teacher grading LMS work after a learner submits.

Return only valid JSON. Do not use markdown code fences.
Output format:
{{
  "summary_feedback": "...",
  "answers": [
    {{
      "question_id": "...",
      "explanation": "...",
      "feedback": "...",
      "score": 0.0
    }}
  ]
}}

Rules:
1. Write in Vietnamese.
2. For every question, explain the answer in enough detail for the learner to understand the reasoning, but do not be verbose. Prefer 2-4 focused sentences.
3. For multiple-choice questions, explain why the correct answer is reasonable and, if the learner chose incorrectly, identify the key misconception without over-explaining.
4. For essay questions, grade primarily by semantic correctness and the learner's core idea. Do not penalize heavily just because wording, structure, order of ideas, terminology, or completeness differs from the expected answer.
5. For essay questions, award high or full credit when the learner's answer is meaningfully correct or shows the right reasoning, even if it is shorter or not phrased like the expected answer.
6. Penalize essay answers mainly for substantive conceptual errors, missing central ideas, unsupported claims, or reasoning that would lead to a wrong conclusion.
7. For essay feedback, state what is correct first, then give concrete corrections or additions only where needed.
8. score must be between 0 and 1 for each question.
9. Include exactly one answers item for every submitted question_id.
10. Keep feedback concise, specific, and actionable; avoid generic praise or long lectures.

Course context:
{course_context}

Scope context:
{scope_context}

Submitted answers:
{submission_context}
""".strip()
