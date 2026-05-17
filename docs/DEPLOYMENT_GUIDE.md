# Deployment Guide

## Requirements

- Linux host with Docker and Docker Compose.
- Production `.env`.
- Persistent PostgreSQL and backend storage volumes.
- Gemini API key if real AI workflows are enabled.

## Environment

```env
DB_USER=lms_user
DB_PASSWORD=strong-password
DB_NAME=lms_db
SECRET_KEY=strong-random-secret-at-least-32-chars
CORS_ORIGINS=https://your-domain
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
GOOGLE_AI_API_KEY=your_google_ai_studio_key
```

`docker-compose.prod.yml` leaves `NEXT_PUBLIC_API_URL` empty so frontend calls
same-origin Nginx.

## Deploy

```bash
git pull
cp .env.example .env   # first deploy only, then edit
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Open:

- App: `http://your-host`
- API docs: `http://your-host/docs`
- Health: `http://your-host/health`

## Helper Script

```bash
./deploy.sh
```

The script checks Docker, creates `.env` if missing, builds, starts services,
runs migrations, waits for health, and creates demo users. Its generated `.env`
uses `LLM_PROVIDER=mock` for smoke deployments; review before production use.

## GitHub Actions Deployment

The repo includes two workflows:

- `.github/workflows/ci.yml`: backend tests, frontend build, and production
  Compose build validation.
- `.github/workflows/deploy.yml`: SSH deployment to one production host.

Deployment runs in either case:

- Manual: run the `Deploy` workflow from GitHub Actions and choose `ref`.
- Automatic: push to `main`, CI succeeds, and repository variable
  `ENABLE_PRODUCTION_DEPLOY=true`.

Target server requirements:

- Git, Docker, and Docker Compose installed.
- SSH user can run Docker commands.
- App directory is empty, absent, or already a git checkout.

Required secrets:

- `PRODUCTION_SSH_HOST`
- `PRODUCTION_SSH_USER`
- `PRODUCTION_SSH_PRIVATE_KEY`
- `PRODUCTION_ENV_FILE`

Optional secrets:

- `PRODUCTION_SSH_PORT` defaults to `22`.
- `PRODUCTION_SSH_KNOWN_HOSTS`; if omitted, workflow uses `ssh-keyscan`.

Optional repository variables:

- `ENABLE_PRODUCTION_DEPLOY=true` enables automatic deploy after CI.
- `PRODUCTION_APP_DIR` defaults to `/opt/ai-lms`.
- `PRODUCTION_REPO_URL` defaults to the current GitHub repository URL.
- `PRODUCTION_HEALTHCHECK_URL` defaults to `http://localhost/health`.

`PRODUCTION_ENV_FILE` should contain the full production `.env` content, for
example:

```env
DB_USER=lms_user
DB_PASSWORD=strong-password
DB_NAME=lms_db
SECRET_KEY=strong-random-secret-at-least-32-chars
CORS_ORIGINS=https://your-domain
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite
GOOGLE_AI_API_KEY=your_google_ai_studio_key
```

Workflow steps:

1. Verify required secrets.
2. Configure SSH.
3. Clone or update the repo on the server.
4. Upload `PRODUCTION_ENV_FILE` to `$PRODUCTION_APP_DIR/.env`.
5. Build and restart `docker-compose.prod.yml`.
6. Run `alembic upgrade head`.
7. Restart Nginx.
8. Check backend and frontend health; on failure, print recent service logs.

## Logs

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend frontend nginx db
```

## Backup

Back up PostgreSQL and storage together:

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U "$DB_USER" "$DB_NAME" > ai_lms.sql
docker run --rm -v ai-lms_storage_data:/data -v "$PWD:/backup" alpine tar czf /backup/storage_data.tgz /data
```

Check the real volume name with `docker volume ls`.

## Update

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml restart nginx
```

## Notes

- Nginx `/api/` timeouts are long for AI calls.
- Rotate `SECRET_KEY` carefully; existing JWTs become invalid.
- `LLM_PROVIDER=mock` is for smoke tests, not realistic structured generation.
- Do not expose open role selection in production without access controls.
