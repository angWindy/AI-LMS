# Setup Guide

## Requirements

- Docker and Docker Compose.
- Python 3.11+ for backend/tests.
- Node.js 20+ for frontend development.

## Environment

```bash
cp .env.example .env
```

Root `.env` is used by Docker Compose. If running backend directly from
`apps/backend`, export the same variables or create `apps/backend/.env`.

Frontend local dev:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Default AI model:

```env
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
GOOGLE_AI_API_KEY=your_google_ai_studio_key
```

Use `LLM_PROVIDER=mock` for offline smoke work.

## Development Stack

Start database and backend:

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Run frontend:

```bash
cd apps/frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Backend On Host

```bash
docker compose up -d db
cd apps/backend
python -m pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Default local database URL:

```text
postgresql://lms_user:lms_password@localhost:5432/lms_db
```

## Production-Like Local Stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

URLs:

- App: `http://localhost`
- API docs: `http://localhost/docs`
- Health: `http://localhost/health`

## Demo Users

The API allows registration with a requested role, useful for local dev. Demo
users can also be created inside the backend container:

```bash
docker compose -f docker-compose.prod.yml exec backend python scripts/create_demo_users.py
```

Created users:

```text
admin@test.com / 00000000
teacher@test.com / 00000000
student@test.com / 00000000
```

Do not expose unrestricted role selection in production without product-level
controls.

## Tests

```bash
python -m pip install -r apps/backend/requirements-dev.txt
PYTHONPATH="$PWD:$PWD/apps/backend" LLM_PROVIDER=mock python -m pytest -q tests
```

Frontend:

```bash
cd apps/frontend
npm ci
npm run build
npm run lint
```

## Troubleshooting

- Missing tables: run `alembic upgrade head`.
- Frontend cannot reach API: set `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- AI key error: set `GOOGLE_AI_API_KEY` or use `LLM_PROVIDER=mock`.
- RAG not indexing: verify PDF/DOCX input, Gemini key, and pgvector extension.
