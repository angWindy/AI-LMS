# AI-LMS Documentation

These docs summarize the current implementation. Source of truth remains the
code in `apps/`, `llm/`, migrations, and Compose files.

## Core

- [Architecture](ARCHITECTURE.md)
- [Setup Guide](SETUP_GUIDE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Database Schema Notes](DATABASE_SCHEMA.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md): manual deploy, helper script, and
  GitHub Actions deployment.
- [Course Levels](COURSE_LEVELS.md)

## Features

- [Assignments And Tests](ASSIGNMENTS_AND_TESTS.md)
- [Question Bank](QUESTION_BANK.md)
- [RAG System](RAG.md)
- [Chatbot](CHATBOT.md)

## Source Map

- Backend app: `apps/backend/app/main.py`
- API routers: `apps/backend/app/api/v1/`
- Models: `apps/backend/app/models/`
- Schemas: `apps/backend/app/schemas/`
- Services: `apps/backend/app/services/`
- Frontend routes: `apps/frontend/src/app/`
- Frontend API clients: `apps/frontend/src/lib/api/`
- LLM prompts/workflows: `llm/prompts/`, `llm/workflows/`
- RAG pipeline: `llm/rag/`
- Tests: `tests/`
