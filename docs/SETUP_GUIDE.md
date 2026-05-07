# Setup Guide

## Prerequisites

- **Docker** & **Docker Compose**
- **Git**
- **Make** (optional)

OS: Linux, macOS, or Windows (WSL2)

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd AI-LMS
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Default values work for local development. Edit if needed.

### 3. Start Application

```bash
make start
```

This will:
- Start PostgreSQL container
- Run database migrations automatically  
- Start FastAPI backend

### 4. Verify

Open browser:
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Common Tasks

### View Logs

```bash
docker-compose logs -f        # All services
docker-compose logs -f backend # Just backend
docker-compose logs -f db     # Just database
```

### Stop Services

```bash
make stop
# or
docker-compose down
```

### Reset Database

```bash
docker-compose down -v   # Remove volumes
make start              # Restart with clean DB
```

### Run Migrations Manually

```bash
docker-compose exec backend alembic upgrade head
```

### Access Database

```bash
docker-compose exec db psql -U postgres -d ailms
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Change ports in .env or docker-compose.yml if needed
```

### Migration Errors

```bash
docker-compose exec backend alembic upgrade head
# Or restart clean:
docker-compose down -v && make start
```

### Docker Issues

```bash
docker-compose build --no-cache   # Rebuild
docker image prune -a             # Clean images
docker ps                          # Check running containers
```

### Database Connection Error

```bash
docker-compose ps                # Check status
docker-compose logs db           # View logs
docker-compose restart db        # Restart
```

---

## Development Workflow

### Make Commands

```bash
make start       # Start all services
make stop        # Stop services
make logs        # View logs
make clean       # Clean up
```

### Without Make

```bash
docker-compose up -d           # Start background
docker-compose logs -f         # View logs  
docker-compose down            # Stop everything
```

---

## API Testing

### Swagger UI

1. Go to http://localhost:8000/docs
2. Click "Authorize"
3. Enter your JWT token
4. Try any endpoint

### cURL

```bash
# Login
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ailms.com","password":"Admin123!"}')

TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users
```

### Python

```python
import requests

response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'admin@ailms.com',
    'password': 'Admin123!'
})
token = response.json()['access_token']

headers = {'Authorization': f'Bearer {token}'}
users = requests.get('http://localhost:8000/api/v1/users', headers=headers)
print(users.json())
```

---

## Environment Variables

Key variables in `.env`:

```
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=ailms

API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key

# LLM (Google Gemini)
LLM_PROVIDER=google
LLM_MODEL=gemini-3.1-flash-lite-preview
LLM_TEMPERATURE=0.1
LLM_MAX_OUTPUT_TOKENS=512
# LLM_THINKING_LEVEL applies to Gemini models only
# - gemini-3.1-flash-lite-preview
# - gemini-2.5-flash
# Leave empty for gemma-4-31b-it
# LLM_THINKING_LEVEL=low
GOOGLE_AI_API_KEY=your_google_ai_studio_key
GOOGLE_AI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta
```

---

## Next Steps

1. ✅ Setup complete
2. Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
3. Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
4. Test via Swagger UI

**Last Updated**: 2026-03-29
