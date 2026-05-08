"""Tests for slide generator prompt helpers."""

from llm.prompts.slide_generator import (
    build_document_to_ir_prompt,
    build_ir_to_slides_prompt,
)


def test_document_to_ir_prompt_contains_ir_schema() -> None:
    prompt = build_document_to_ir_prompt(
        course_context="Course title: Intro AI",
        lesson_context="Lesson title: Search",
    )

    assert '"document_title"' in prompt
    assert '"key_concepts"' in prompt
    assert '"main_sections"' in prompt
    assert '"teaching_suggestions"' in prompt
    assert '"relationships"' not in prompt
    assert '"assessment_items"' not in prompt
    assert '"source_constraints"' not in prompt


def test_prompts_require_valid_json_without_markdown_fences() -> None:
    ir_prompt = build_document_to_ir_prompt(
        course_context="Course title: Intro AI",
        lesson_context="Lesson title: Search",
    )
    slide_prompt = build_ir_to_slides_prompt(
        ir_json='{"document_title": "Search", "main_sections": [{"id": 1}]}',
        slide_count=5,
    )

    for prompt in (ir_prompt, slide_prompt):
        assert "valid JSON" in prompt
        assert "Do not use markdown code fences" in prompt


def test_prompts_allow_general_teaching_knowledge() -> None:
    ir_prompt = build_document_to_ir_prompt(
        course_context="Course title: Intro AI",
        lesson_context="Lesson title: Search",
    )
    slide_prompt = build_ir_to_slides_prompt(
        ir_json='{"document_title": "Search", "main_sections": [{"id": 1}]}',
        slide_count=5,
    )

    assert "general domain and teaching knowledge" in ir_prompt
    assert "general teaching knowledge" in slide_prompt


def test_ir_to_slides_prompt_contains_slide_count_and_type_enum() -> None:
    prompt = build_ir_to_slides_prompt(
        ir_json='{"document_title": "Search", "main_sections": [{"id": 1}]}',
        slide_count=7,
    )

    assert "Generate exactly 7 slides" in prompt
    assert "slides array length must equal 7" in prompt
    assert "title, objectives, concept, comparison, example" in prompt
    assert "summary, quiz" in prompt
