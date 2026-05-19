"""Prompt helpers for slide generation workflows."""

from llm.prompts.learning_level import build_learning_level_instructions


def build_document_to_ir_prompt(
  course_context: str,
  lesson_context: str,
  course_level: str | None = None,
) -> str:
    """Build a strict prompt that converts lesson context into document IR JSON."""
  level_guidance = build_learning_level_instructions(course_level)
    return f"""
You are an expert Vietnamese curriculum designer.
Convert the course and lesson context into a JSON Intermediate Representation (IR)
for lecture slide generation.

Strict output rules:
1. Return ONLY valid JSON. Do not use markdown code fences.
2. Output must be in Vietnamese.
3. Prioritize the information present in the course context and lesson context.
4. You may use your own general domain and teaching knowledge to clarify,
   explain, or add simple examples when the context is thin.
5. Do not invent specific course facts, citations, statistics, source names, or
   claims that are not supported by either context or widely accepted knowledge.
6. Do not create slides in this step. Create only the IR object.
7. Keep the IR compact and useful for a teacher-facing lecture slide deck.
8. Align wording and examples with the learner level guidance below.

Learner level guidance:
{level_guidance}

Required JSON schema:
{{
  "document_title": "...",
  "domain": "...",
  "summary": "...",
  "learning_objectives": ["..."],
  "key_concepts": [
    {{
      "name": "...",
      "definition": "...",
      "importance": "...",
      "examples": ["..."]
    }}
  ],
  "main_sections": [
    {{
      "id": 1,
      "heading": "...",
      "summary": "...",
      "key_points": ["..."],
      "examples": ["..."],
      "teaching_suggestions": ["..."],
      "possible_visuals": ["..."]
    }}
  ]
}}

Field guidance:
- document_title should come from the lesson title when available; otherwise use
  the most specific supported title from the source context.
- domain should be inferred from course and lesson context when possible.
- main_sections.id must start at 1 and increase sequentially.
- key_points should stay close to the source context.
- definitions, examples, and teaching_suggestions may use general LLM knowledge
  when that helps explain the lesson clearly.
- possible_visuals should describe useful visual ideas only, not renderer or PDF
  implementation details.

Course context:
{course_context}

Lesson context:
{lesson_context}
""".strip()


def build_ir_to_slides_prompt(
  ir_json: str,
  slide_count: int,
  course_level: str | None = None,
) -> str:
    """Build a strict prompt that converts document IR JSON into slides JSON."""
  level_guidance = build_learning_level_instructions(course_level)
    return f"""
You are an expert Vietnamese teacher assistant.
Convert the JSON IR into lecture slides JSON. The JSON IR is the source of truth.
Generate exactly {slide_count} slides in Vietnamese.

Strict output rules:
1. Return ONLY valid JSON. Do not use markdown code fences.
2. Output must be in Vietnamese.
3. Use the JSON IR as the primary source of truth.
4. You may use general teaching knowledge to clarify wording, but do not add
  unsupported specific facts or citations.
5. The slides array length must equal {slide_count}.
6. id must start at 1 and increase sequentially.
7. slide_type must be one of: title, objectives, concept, comparison, example,
   summary, quiz.
8. content must be concise bullet points as short strings, but still complete
  enough to convey the full idea without being verbose.
9. source_sections must contain only main_sections.id values present in the IR.
10. Avoid duplicated content across slides.
11. Do not include design, theme, UI, renderer, export, or PDF instructions.
12. Keep tone and depth aligned with the learner level guidance below.

Learner level guidance:
{level_guidance}

Required JSON schema:
{{
  "document_type": "slides",
  "title": "...",
  "slides": [
    {{
      "id": 1,
      "slide_type": "title",
      "title": "...",
      "content": ["..."],
      "source_sections": [1]
    }}
  ]
}}

JSON IR source of truth:
{ir_json}
""".strip()
