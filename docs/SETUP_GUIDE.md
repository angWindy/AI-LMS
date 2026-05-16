# Setup Guide

## Requirements

- Docker and Docker Compose.
- Git.
- Python 3.11+ for backend tests or local backend execution.
- Node.js 18+ for frontend development.

## Environment

Create `.env` at the repo root.

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/ai_lms
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60

LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=512
LLM_THINKING_LEVEL=
GOOGLE_AI_API_KEY=your-key
```

Use `LLM_PROVIDER=mock` when you do not want network LLM calls.

## Docker Run

```bash
docker compose up -d --build
docker compose ps
```

Open:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Backend Local Run

```bash
cd apps/backend
python -m pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Frontend Local Run

```bash
cd apps/frontend
npm install
npm run dev
```

## Tests

```bash
python -m pytest -q tests
```
