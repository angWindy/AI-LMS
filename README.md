# AI-LMS

AI-LMS is a monorepo learning management system with AI-assisted course
authoring and tutoring.

## Scope

- Roles: `admin`, `instructor`, `learner`.
- Courses, lessons, course/lesson materials, and lesson progress.
- Question Bank with reusable multiple-choice questions.
- Practice assignments from AI or Question Bank.
- Course-level tests from assessment-ready Question Bank items.
- Learner submissions with automatic scoring and AI feedback.
- RAG over uploaded PDF/DOCX materials.
- General chatbot and assignment hint chatbot.

There is no active enrollment module. Published courses, published lessons, and
published assignments are the current learner-facing boundary.

## Stack

- Backend: FastAPI, SQLAlchemy 2, Alembic, Pydantic v2.
- Frontend: Next.js 14 App Router, TypeScript, Tailwind CSS, Zustand, Axios.
- Database: PostgreSQL 15 with pgvector.
- AI: Google Gemini via `llm/`, default model `gemini-3.1-flash-lite`; `mock`
  provider for offline smoke tests.
- Storage: local filesystem under `STORAGE_PATH`, served from `/storage`.

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Run the frontend locally:

```bash
cd apps/frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Development URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Production-like full stack:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Production-like URLs:

- App: `http://localhost`
- API docs: `http://localhost/docs`
- Health: `http://localhost/health`

## Useful Commands

```bash
make test
docker compose -f docker-compose.prod.yml logs -f backend frontend nginx db
docker compose -f docker-compose.prod.yml exec backend python scripts/create_demo_users.py
```

Use `LLM_PROVIDER=mock` without external AI calls. Use `LLM_PROVIDER=google`
with `GOOGLE_AI_API_KEY` for generation, chatbot, RAG embeddings, and feedback.

## Documentation

- [Docs Index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup](docs/SETUP_GUIDE.md)
- [API](docs/API_DOCUMENTATION.md)
- [Database](docs/DATABASE_SCHEMA.md)
- [Assignments And Tests](docs/ASSIGNMENTS_AND_TESTS.md)
- [Question Bank](docs/QUESTION_BANK.md)
- [RAG](docs/RAG.md)
- [Chatbot](docs/CHATBOT.md)
- [Deployment](docs/DEPLOYMENT_GUIDE.md): manual and GitHub Actions deployment.
