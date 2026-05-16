# Slide Generation

Slide Generation creates lecture decks for lessons.

## Access

- Admin and Instructor can generate, preview, publish, and delete decks.
- Learners can access published decks through lesson content.

## Flow

1. Backend builds course and lesson context.
2. LLM creates a document intermediate representation.
3. LLM converts that representation into slide JSON.
4. Backend renders a PDF.
5. The deck is saved as unpublished by default.

## Main Files

- Prompts: `llm/prompts/slide_generator.py`
- Workflow: `llm/workflows/slide_generator.py`
- Service: `apps/backend/app/services/slide_generator_service.py`
- API: `apps/backend/app/api/v1/slides.py`
- Tests: `tests/test_slide_generator_prompts.py`, `tests/test_slide_pdf_render.py`

## API

```text
POST /api/v1/slides/generate-draft?course_id={course_id}
GET /api/v1/slides?course_id={course_id}
GET /api/v1/slides/{slide_deck_id}
POST /api/v1/slides/{slide_deck_id}/publish
DELETE /api/v1/slides/{slide_deck_id}
```

## Output

Each deck stores:

- title
- course and lesson references
- slide JSON
- PDF path
- provider/model metadata
- publish status

## Tests

```bash
python -m pytest -q tests/test_slide_generator_prompts.py tests/test_slide_pdf_render.py
```

## Limits

- No visual slide editor.
- No theme system.
- No version comparison UI.
- Long LLM calls require frontend, backend, and proxy timeouts to allow several minutes.
