# Slide Generation

AI-generated lecture slide decks for lessons. Each deck stores IR JSON, slide
JSON, provider/model metadata, and a PDF URL.

## Access

- Admin/instructor: generate, publish, delete.
- Learner: read published decks only.

## API

```text
POST   /api/v1/slides/generate-draft?course_id={course_id}
GET    /api/v1/slides?course_id={course_id}&lesson_id={lesson_id}&include_unpublished=false
GET    /api/v1/slides/{slide_deck_id}
POST   /api/v1/slides/{slide_deck_id}/publish
DELETE /api/v1/slides/{slide_deck_id}
```

Generate:

```json
{ "lesson_id": "uuid", "slide_count": 8, "title": "optional" }
```

`slide_count` range: 1 to 50.

## Flow

1. Load course, lesson, and material context.
2. LLM creates document IR, including `learner_level` from the course.
3. LLM converts IR to slide JSON and adapts objectives, vocabulary, examples,
   bullets, and quiz prompts to that level.
4. Backend renders PDF into `/storage`.
5. Deck is saved unpublished.

Slide types: `title`, `objectives`, `concept`, `comparison`, `example`,
`summary`, `quiz`.

## Main Files

- API: `apps/backend/app/api/v1/slides.py`
- Model/schema: `apps/backend/app/models/slide_deck.py`,
  `apps/backend/app/schemas/slide_deck.py`
- Service: `apps/backend/app/services/slide_generator_service.py`
- Prompt/workflow: `llm/prompts/slide_generator.py`,
  `llm/workflows/slide_generator.py`

## Tests

```bash
python -m pytest -q tests/test_slide_generator_prompts.py tests/test_slide_pdf_render.py
```

## Gaps

No visual editor, theme system, or deck version comparison UI.
