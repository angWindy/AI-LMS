# GitHub Actions Deployment

Repo nay co 2 workflow:

- `CI`: chay khi push/pull request vao `main`; kiem tra backend, frontend va Docker Compose production build.
- `Deploy`: deploy production qua SSH. Workflow nay co the chay thu cong, hoac tu dong sau khi `CI` tren `main` thanh cong neu bat repository variable `ENABLE_PRODUCTION_DEPLOY=true`.

## Chuan bi server

Server production can co:

- `git`
- Docker Engine
- Docker Compose plugin (`docker compose version`)
- Mot SSH user co quyen chay Docker
- Port `80` dang trong cho stack nginx cua du an, tru khi ban sua `docker-compose.prod.yml`

Thu muc mac dinh tren server la `/opt/ai-lms`. Co the doi bang repository variable `PRODUCTION_APP_DIR`.

## GitHub Secrets

Vao `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`, them cac secret sau:

| Secret | Bat buoc | Mo ta |
| --- | --- | --- |
| `PRODUCTION_SSH_HOST` | Co | IP hoac hostname server |
| `PRODUCTION_SSH_USER` | Co | SSH user dung de deploy |
| `PRODUCTION_SSH_PRIVATE_KEY` | Co | Private key SSH co quyen vao server |
| `PRODUCTION_ENV_FILE` | Co | Toan bo noi dung file `.env` production |
| `PRODUCTION_SSH_PORT` | Khong | SSH port, mac dinh `22` |
| `PRODUCTION_SSH_KNOWN_HOSTS` | Khong | Noi dung known_hosts da verify. Neu bo trong, workflow se dung `ssh-keyscan` |

`PRODUCTION_ENV_FILE` nen co dang:

```env
DB_USER=lms_user
DB_PASSWORD=change-this-strong-password
DB_NAME=lms_db

SECRET_KEY=change-this-strong-secret-at-least-32-chars
CORS_ORIGINS=https://your-domain.com,http://localhost,http://nginx
MAX_DOCUMENT_SIZE_MB=100
LOG_LEVEL=INFO

GOOGLE_AI_API_KEY=change-this-google-ai-key
GOOGLE_AI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=512
LLM_THINKING_LEVEL=
```

Khong commit file `.env` production vao repo.

## GitHub Variables

Vao `Settings` -> `Secrets and variables` -> `Actions` -> tab `Variables`, them neu can:

| Variable | Gia tri mac dinh | Mo ta |
| --- | --- | --- |
| `ENABLE_PRODUCTION_DEPLOY` | khong bat | Dat `true` de deploy tu dong sau CI tren `main` |
| `PRODUCTION_APP_DIR` | `/opt/ai-lms` | Thu muc source tren server |
| `PRODUCTION_REPO_URL` | URL repo hien tai | URL git ma server se clone/fetch |
| `PRODUCTION_HEALTHCHECK_URL` | `http://localhost/health` | URL health check chay tren server sau deploy |

## Cach chay deploy

Chay thu cong:

1. Vao tab `Actions`.
2. Chon workflow `Deploy`.
3. Chon `Run workflow`.
4. Giu `ref=main` hoac nhap branch/tag can deploy.

Bat deploy tu dong:

1. Dam bao workflow `CI` dang xanh tren `main`.
2. Them repository variable `ENABLE_PRODUCTION_DEPLOY=true`.
3. Tu lan push tiep theo vao `main`, workflow `Deploy` se chay sau khi `CI` thanh cong.

## Workflow deploy lam gi

1. SSH vao server.
2. Clone repo vao `PRODUCTION_APP_DIR` neu chua co, hoac fetch/reset source neu da co.
3. Upload noi dung `PRODUCTION_ENV_FILE` thanh file `.env` tren server.
4. Chay `docker compose -f docker-compose.prod.yml build`.
5. Chay `docker compose -f docker-compose.prod.yml up -d --remove-orphans`.
6. Chay migration bang `alembic upgrade head`.
7. Kiem tra health check.
