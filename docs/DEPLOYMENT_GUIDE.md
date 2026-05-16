# Deployment Guide

## Requirements

- Linux server with Docker and Docker Compose.
- Domain or IP address.
- `.env` with production secrets.
- Gemini API key if AI generation is enabled.

## Environment Checklist

```env
DATABASE_URL=postgresql://...
SECRET_KEY=strong-secret
BACKEND_CORS_ORIGINS=https://your-domain
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
GOOGLE_AI_API_KEY=your-key
```

## Deploy

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Migrations

Run migrations inside the backend container when needed:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Logs

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f nginx
```

## Update

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Rollback

```bash
git checkout <previous-sha>
docker compose -f docker-compose.prod.yml up -d --build
```

Database rollback is migration-specific; inspect the Alembic revision before downgrading.
