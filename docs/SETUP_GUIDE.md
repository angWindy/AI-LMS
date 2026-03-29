# Setup Guide - AI-LMS

Hướng dẫn cài đặt và triển khai dự án AI-LMS từ đầu.

## Yêu cầu hệ thống

### Phần mềm bắt buộc

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **Git**: Latest version
- **Text Editor**: VS Code (recommended) hoặc editor khác

### Hệ điều hành hỗ trợ

- Linux (Ubuntu 20.04+, Debian 11+)
- macOS (Big Sur 11.0+)
- Windows 10/11 (với WSL2)

### Phần cứng khuyến nghị

- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB+
- **CPU**: 2 cores trở lên
- **Disk**: 10GB available space
- **Network**: Kết nối internet ổn định

---

## Bước 1: Cài đặt Docker

### Linux (Ubuntu/Debian)

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Add current user to docker group (optional, để chạy docker không cần sudo)
sudo usermod -aG docker $USER
# Log out and log back in for this to take effect
```

### macOS

```bash
# Install Docker Desktop from:
# https://www.docker.com/products/docker-desktop

# Or using Homebrew:
brew install --cask docker

# Verify installation
docker --version
docker compose version
```

### Windows (WSL2)

1. Install WSL2: https://docs.microsoft.com/en-us/windows/wsl/install
2. Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop
3. Enable WSL2 backend in Docker Desktop settings
4. Verify in WSL2 terminal:
   ```bash
   docker --version
   docker compose version
   ```

---

## Bước 2: Clone Repository

```bash
# Clone the project
git clone https://github.com/your-org/AI-LMS.git
cd AI-LMS

# Check project structure
ls -la
```

**Expected output:**
```
.env.example
.gitignore
Makefile
README.md
apps/
docker/
docker-compose.yml
docs/
packages/
services/
tests/
```

---

## Bước 3: Cấu hình Environment Variables

### 3.1. Copy file .env mẫu

```bash
make setup
# OR manually:
cp .env.example .env
```

### 3.2. Chỉnh sửa file .env

Mở file `.env` và cập nhật các giá trị:

```bash
# Database Configuration
DB_USER=lms_user
DB_PASSWORD=your_secure_password_here    # ⚠️ CHANGE THIS!
DB_NAME=lms_db
DB_HOST=db
DB_PORT=5432

# Application
SECRET_KEY=your-secret-key-at-least-32-characters-long-change-this    # ⚠️ CHANGE THIS!
ENVIRONMENT=development
DEBUG=true

# Backend
BACKEND_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Storage
STORAGE_PATH=/app/storage
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes

# Email (Optional - for future features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@ailms.com
```

### 3.3. Generate Secret Key

**Cách 1: Sử dụng Python**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Cách 2: Sử dụng OpenSSL**
```bash
openssl rand -hex 32
```

Copy output và paste vào `SECRET_KEY` trong file `.env`.

---

## Bước 4: Build và Start Services

### 4.1. Build Docker Images

```bash
make build
# OR manually:
docker-compose build
```

**Expected output:**
```
Building backend...
[+] Building 45.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 ...
 => exporting to image
 => => writing image sha256:...
 => => naming to docker.io/library/ai-lms_backend
```

### 4.2. Start Services

```bash
make start
# OR manually:
docker-compose up -d
```

**Expected output:**
```
Creating network "ai-lms_lms_network" with driver "bridge"
Creating volume "ai-lms_postgres_data" with local driver
Creating volume "ai-lms_storage_data" with local driver
Creating lms_db ... done
Creating lms_backend ... done
✓ Services started
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### 4.3. Verify Services

```bash
# Check running containers
docker-compose ps
```

**Expected output:**
```
NAME            IMAGE                   STATUS          PORTS
lms_backend     ai-lms_backend          Up 30 seconds   0.0.0.0:8000->8000/tcp
lms_db          postgres:15-alpine      Up 30 seconds   0.0.0.0:5432->5432/tcp
```

### 4.4. Check Logs

```bash
# All services
make logs

# Backend only
make logs-backend

# Database only
docker-compose logs -f db
```

---

## Bước 5: Database Migration

### 5.1. Run Initial Migration

```bash
make migrate
# OR manually:
docker-compose exec backend alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 299a7a8507ce, initial migration
✓ Migrations applied
```

### 5.2. Verify Database

```bash
# Open database shell
make shell-db
# OR manually:
docker-compose exec db psql -U lms_user -d lms_db
```

**Check tables:**
```sql
-- List all tables
\dt

-- Expected output:
             List of relations
 Schema |        Name        | Type  |  Owner   
--------+--------------------+-------+----------
 public | ai_conversations   | table | lms_user
 public | ai_messages        | table | lms_user
 public | alembic_version    | table | lms_user
 public | assignments        | table | lms_user
 public | courses            | table | lms_user
 public | enrollments        | table | lms_user
 public | lesson_progress    | table | lms_user
 public | lessons            | table | lms_user
 public | materials          | table | lms_user
 public | refresh_tokens     | table | lms_user
 public | submissions        | table | lms_user
 public | users              | table | lms_user

-- Exit psql
\q
```

---

## Bước 6: Verify API

### 6.1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### 6.2. API Documentation

Mở browser và truy cập:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 6.3. Create Test User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailms.com",
    "password": "Admin123!",
    "full_name": "System Admin",
    "role": "ADMIN"
  }'
```

**Expected response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "admin@ailms.com",
  "full_name": "System Admin",
  "role": "ADMIN",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-03-29T12:00:00Z"
}
```

### 6.4. Test Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailms.com",
    "password": "Admin123!"
  }'
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "admin@ailms.com",
    "full_name": "System Admin",
    "role": "ADMIN"
  }
}
```

---

## Bước 7: Development Setup (Optional)

Nếu bạn muốn develop mà không dùng Docker:

### 7.1. Install Python Dependencies

```bash
cd apps/backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for development tools
```

### 7.2. Setup Local Database

```bash
# Install PostgreSQL locally (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE lms_db;
CREATE USER lms_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE lms_db TO lms_user;
\q
```

### 7.3. Update .env for Local Development

```bash
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://lms_user:your_password@localhost:5432/lms_db
```

### 7.4. Run Migrations

```bash
cd apps/backend
alembic upgrade head
```

### 7.5. Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Common Commands

### Service Management

```bash
# Start all services
make start

# Stop all services
make stop

# Restart services
make restart

# View logs
make logs
make logs-backend

# Rebuild containers
make build
```

### Database Operations

```bash
# Run migrations
make migrate

# Create new migration
make migration MESSAGE="add new field"

# Open database shell
make shell-db

# Open backend container shell
make shell-backend
```

### Cleanup

```bash
# Stop and remove all containers, volumes
make clean

# Remove all Docker images
docker-compose down --rmi all

# Remove volumes only
docker-compose down -v
```

---

## Troubleshooting

### Problem 1: Port already in use

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solution:**

**Option 1: Change port in .env**
```bash
# Edit .env
BACKEND_PORT=8001
DB_PORT=5433
```

**Option 2: Kill process using the port**
```bash
# Find process
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

---

### Problem 2: Database connection error

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db

# If still failing, recreate database
docker-compose down -v
docker-compose up -d
make migrate
```

---

### Problem 3: Migration errors

**Error:**
```
Target database is not up to date
```

**Solution:**

```bash
# Check current migration
docker-compose exec backend alembic current

# Check pending migrations
docker-compose exec backend alembic heads

# Upgrade to latest
make migrate

# If corrupted, reset (⚠️ will lose data)
make clean
make start
make migrate
```

---

### Problem 4: Permission denied

**Error:**
```
docker: Got permission denied while trying to connect to the Docker daemon socket
```

**Solution:**

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or:
newgrp docker

# Test
docker ps
```

---

### Problem 5: Cannot access API

**Symptoms:**
- curl returns "Connection refused"
- Browser shows "This site can't be reached"

**Solution:**

```bash
# 1. Check if backend is running
docker-compose ps backend

# 2. Check backend logs
make logs-backend

# 3. Check backend health inside container
docker-compose exec backend curl http://localhost:8000/health

# 4. If health check works, check firewall
sudo ufw status
sudo ufw allow 8000

# 5. Restart backend
docker-compose restart backend
```

---

### Problem 6: Slow performance

**Solution:**

```bash
# Check container resources
docker stats

# Check logs for errors
make logs-backend

# Increase Docker memory/CPU in Docker Desktop settings

# Check database connections
docker-compose exec db psql -U lms_user -d lms_db -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## VS Code Setup (Recommended)

### 1. Install Extensions

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Docker** (ms-azuretools.vscode-docker)
- **PostgreSQL** (ckolkman.vscode-postgres)
- **Thunder Client** (rangav.vscode-thunder-client) - for API testing

### 2. Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/apps/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### 3. Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}/apps/backend"
    }
  ]
}
```

---

## Next Steps

Sau khi setup thành công:

1. **Đọc API Documentation**: http://localhost:8000/docs
2. **Tạo test data**: Sử dụng Swagger UI để tạo users, courses, lessons
3. **Khám phá codebase**: Đọc `docs/PROJECT_OVERVIEW.md` và `docs/DEVELOPMENT_GUIDE.md`
4. **Setup Frontend** (nếu cần): Xem hướng dẫn trong `apps/frontend/README.md`
5. **Contribute**: Đọc CONTRIBUTING.md (nếu có)

---

## Production Deployment

⚠️ **Warning**: Configuration hiện tại chỉ dành cho development. Để deploy production:

### Security Checklist

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Change `DB_PASSWORD` to strong password
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Use HTTPS (setup reverse proxy with nginx/traefik)
- [ ] Setup proper backup strategy
- [ ] Configure log management
- [ ] Setup monitoring (Prometheus, Grafana)
- [ ] Use environment variables management (AWS Secrets Manager, etc.)
- [ ] Enable rate limiting
- [ ] Setup CDN for static files
- [ ] Configure proper database connection pooling

### Production Deployment Options

1. **Docker Swarm**
2. **Kubernetes**
3. **AWS ECS/Fargate**
4. **Google Cloud Run**
5. **Azure Container Instances**
6. **Traditional VPS with Docker Compose**

Xem thêm: `docs/DEPLOYMENT_GUIDE.md` (planned)

---

## Support

Nếu gặp vấn đề:

1. Check logs: `make logs-backend`
2. Check database: `make shell-db`
3. Search in docs: `docs/` folder
4. Check API docs: http://localhost:8000/docs
5. Open GitHub issue

---

**Version**: 1.0.0  
**Last Updated**: 2026-03-29
