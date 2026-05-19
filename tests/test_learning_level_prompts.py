"""Tests for learner-level prompt adaptation helpers."""

from llm.prompts.assignment_chatbot import build_assignment_tutor_prompt
from llm.prompts.chatbot import build_lms_chatbot_prompt
from llm.prompts.learning_level import (
    build_learning_level_prompt_block,
    learning_level_label,
    normalize_learning_level,
)


def test_learning_level_normalization_and_labels() -> None:
    assert normalize_learning_level("thcs") == "middle_school"
    assert normalize_learning_level("Trung học phổ thông") == "high_school"
    assert learning_level_label("higher_education") == "Đại học và sau đại học"


def test_learning_level_prompt_block_contains_guidance() -> None:
    prompt_block = build_learning_level_prompt_block("elementary")

    assert "Learner level: Tiểu học (elementary)" in prompt_block
    assert "simple Vietnamese" in prompt_block
    assert "academically correct" in prompt_block


def test_chatbot_prompts_include_course_level_guidance() -> None:
    prompt = build_lms_chatbot_prompt(
        course_title="Khoa học",
        lesson_title="Ánh sáng",
        course_level="elementary",
    )
    assignment_prompt = build_assignment_tutor_prompt(
        course_title="Khoa học",
        lesson_title="Ánh sáng",
        course_level="middle_school",
    )

    assert "Learner level: Tiểu học (elementary)" in prompt
    assert "Adapt every explanation" in prompt
    assert "Learner level: Trung học cơ sở (middle_school)" in assignment_prompt
    assert "Adapt hints" in assignment_prompt
