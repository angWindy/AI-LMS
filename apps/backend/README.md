# AI-LMS Backend

FastAPI backend for auth, course content, assignments, RAG, chat, and AI
generation workflows.

## Structure

```text
app/api/v1/    routers
app/core/      config, security, dependencies, logging, exceptions
app/db/        SQLAlchemy session/base and Alembic migrations
app/models/    ORM models
app/schemas/   Pydantic schemas
app/services/  business logic and AI/RAG orchestration
app/utils/     file helpers
scripts/       demo and utility scripts
```

Entrypoint: `app/main.py`. API prefix: `/api/v1`. Docs: `/docs`.

## Run Locally

```bash
docker compose up -d db
cd apps/backend
python -m pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Config

```env
DATABASE_URL=postgresql://lms_user:lms_password@localhost:5432/lms_db
SECRET_KEY=change-this
CORS_ORIGINS=http://localhost:3000
STORAGE_PATH=./storage
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=512
LLM_REQUEST_TIMEOUT_SECONDS=180
GOOGLE_AI_API_KEY=your-key
```

Use `LLM_PROVIDER=mock` for offline smoke tests.

## Main Areas

- Auth and refresh tokens.
- Admin user management.
- Courses, lessons, materials, lesson progress.
- Question Bank and AI question generation.
- Assignments, tests, submissions, AI feedback.
- Slide generation and PDF rendering.
- RAG upload/search/stats.
- General and assignment chatbot.

## Database

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
```

## Demo Users

```bash
python scripts/create_demo_users.py
```

Creates `admin@test.com`, `teacher@test.com`, `student@test.com` with password
`00000000`.

## Tests

From repo root:

```bash
PYTHONPATH="$PWD:$PWD/apps/backend" LLM_PROVIDER=mock python -m pytest -q tests
```

Focused:

```bash
python -m pytest -q tests/test_question_generation_metadata.py
python -m pytest -q tests/test_slide_generator_prompts.py tests/test_slide_pdf_render.py
python -m pytest -q tests/test_chatbot_context_selection.py
```
