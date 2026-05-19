"""Tests for generated question metadata distribution."""

# ruff: noqa: E402

import json
from pathlib import Path
import sys
from types import SimpleNamespace

BACKEND_PATH = Path(__file__).resolve().parents[1] / "apps" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

import pytest  # noqa: E402

from app.api.v1.question_bank import assign_purposes_by_difficulty  # noqa: E402
from app.models.assignment import QuestionDifficulty, QuestionPurposeType  # noqa: E402
from app.services.assignment_generator_service import AssignmentGeneratorService  # noqa: E402
from llm.prompts.assignment_generator import (
    build_assignment_generator_prompt,
    difficulty_distribution,
)  # noqa: E402


def test_difficulty_distribution_uses_40_40_20_ratio() -> None:
    assert difficulty_distribution(10) == {"easy": 4, "medium": 4, "hard": 2}
    assert difficulty_distribution(5) == {"easy": 2, "medium": 2, "hard": 1}


def test_assignment_generator_prompt_requires_difficulty_metadata() -> None:
    prompt = build_assignment_generator_prompt(
        question_count=10,
        course_context="Title: AI",
        lesson_context="Title: Search",
    )

    assert '"difficulty": "..."' in prompt
    assert '4 "easy", 4 "medium", 2 "hard"' in prompt
    assert "Tests basic knowledge and recall" in prompt
    assert "Tests understanding and application" in prompt
    assert "Tests analysis and deeper reasoning" in prompt
    assert "Adapt every question, option, distractor" in prompt


def test_parse_questions_preserves_valid_difficulty_distribution() -> None:
    service = AssignmentGeneratorService.__new__(AssignmentGeneratorService)
    raw_questions = [
        {
            "id": index,
            "question": f"Câu hỏi {index}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "difficulty": difficulty,
            "type": "text",
        }
        for index, difficulty in enumerate(
            ["easy", "easy", "medium", "medium", "hard"],
            start=1,
        )
    ]

    questions = service._parse_questions(json.dumps({"questions": raw_questions}), expected_count=5)

    assert [question.difficulty for question in questions] == [
        QuestionDifficulty.EASY,
        QuestionDifficulty.EASY,
        QuestionDifficulty.MEDIUM,
        QuestionDifficulty.MEDIUM,
        QuestionDifficulty.HARD,
    ]


def test_parse_questions_rejects_wrong_difficulty_distribution() -> None:
    service = AssignmentGeneratorService.__new__(AssignmentGeneratorService)
    raw_questions = [
        {
            "id": index,
            "question": f"Câu hỏi {index}?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "difficulty": "easy",
            "type": "text",
        }
        for index in range(1, 6)
    ]

    with pytest.raises(ValueError, match="difficulty distribution"):
        service._parse_questions(json.dumps({"questions": raw_questions}), expected_count=5)


def test_purpose_assignment_uses_ratio_within_each_difficulty_group() -> None:
    questions = [
        SimpleNamespace(difficulty=QuestionDifficulty.EASY)
        for _ in range(20)
    ] + [
        SimpleNamespace(difficulty=QuestionDifficulty.MEDIUM)
        for _ in range(20)
    ]

    purposes = assign_purposes_by_difficulty(questions)

    for start in (0, 20):
        group = purposes[start : start + 20]
        assert group.count(QuestionPurposeType.PRACTICE) == 13
        assert group.count(QuestionPurposeType.SHARED) == 3
        assert group.count(QuestionPurposeType.ASSESSMENT) == 4
