# AI-LMS Backend

FastAPI backend for AI-LMS.

## Structure

```text
app/
  api/v1/       API routers
  core/         config, security, dependencies
  db/           session, base, migrations
  models/       SQLAlchemy models
  schemas/      Pydantic schemas
  services/     business logic
  utils/        helpers
scripts/        smoke tests and utilities
storage/        uploaded/generated files
```

## Local Run

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

API docs:

```text
http://localhost:8000/docs
```

## LLM Configuration

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=512
LLM_THINKING_LEVEL=
GOOGLE_AI_API_KEY=your-key
```

Use `LLM_PROVIDER=mock` for offline development.

## Main AI Features

- Chatbot routes for classroom and assignment help.
- Question generation through `AssignmentGeneratorService`.
- Question Bank generation with backend-validated difficulty distribution.
- Slide generation and PDF rendering.
- RAG ingestion and retrieval.

## Tests

From repo root:

```bash
python -m pytest -q tests
```

Focused backend-related tests:

```bash
python -m pytest -q tests/test_question_generation_metadata.py
python -m pytest -q tests/test_slide_generator_prompts.py
```
