# AI-LMS

AI-LMS is a learning management system built with FastAPI, Next.js, PostgreSQL, and Gemini-powered AI workflows.

## What Is Included

- Course, lesson, material, enrollment, and assignment management.
- Question Bank for reusable multiple-choice questions.
- AI question generation with one prompt per question set.
- AI slide generation with structured JSON and PDF output.
- RAG support for PDF ingestion and course-aware chatbot answers.
- Docker Compose setup for local and production-like runs.

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL, pgvector.
- Frontend: Next.js 14, TypeScript, Tailwind CSS.
- AI: Google Gemini through the shared `llm/` provider abstraction.
- Storage: local upload folders by default.

## Quick Start

```bash
cp .env.example .env  # if available, otherwise create .env from docs/SETUP_GUIDE.md
docker compose up -d --build
```

Useful URLs:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Development Commands

```bash
# Backend tests used in this repo
python -m pytest -q tests

# Backend app, if running without Docker
cd apps/backend
uvicorn app.main:app --reload

# Frontend, if Node.js is installed
cd apps/frontend
npm install
npm run dev
```

## Documentation

- [Documentation Index](docs/README.md)
- [Setup Guide](docs/SETUP_GUIDE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Question Bank](docs/QUESTION_BANK.md)
- [Slide Generation](docs/SLIDE_GENERATION.md)
- [RAG System](docs/RAG.md)

## Current Notes

- Generated Question Bank sets use difficulty distribution `easy/medium/hard = 40/40/20`.
- Question purpose is assigned after generation by backend as `practice/shared/assessment = 65/15/20` within each difficulty group.
- Generated assignment drafts reuse the same question generator and validation path.
