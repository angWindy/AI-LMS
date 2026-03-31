.PHONY: help setup start stop create-users restart logs build clean migrate migration test lint format prod prod-stop prod-logs

# Default target
help:
	@echo "AI-LMS - Available Commands:"
	@echo ""
	@echo "  🚀 Quick Start:"
	@echo "    make start          - Build và start toàn bộ hệ thống (Production)"
	@echo "    make create-users   - Tạo tài khoản mặc định (admin/teacher/student)"
	@echo "    make stop           - Dừng tất cả services"
	@echo ""
	@echo "  📊 Monitoring:"
	@echo "    make logs           - Xem logs tất cả services"
	@echo "    make logs-backend   - Xem logs backend"
	@echo "    make logs-frontend  - Xem logs frontend"
	@echo ""
	@echo "  🔄 Management:"
	@echo "    make restart        - Restart services"
	@echo "    make rebuild        - Rebuild và restart"
	@echo "    make clean          - Xóa containers và volumes"
	@echo ""
	@echo "  🗄️  Database:"
	@echo "    make migrate        - Chạy database migrations"
	@echo "    make migration      - Tạo migration mới"
	@echo "    make shell-db       - Mở PostgreSQL shell"
	@echo ""
	@echo "  🔧 Development:"
	@echo "    make shell-backend  - Truy cập backend shell"
	@echo "    make shell-frontend - Truy cập frontend shell"
	@echo ""

# Start services (Production mode with all components)
start:
	@echo "🚀 Building and starting AI-LMS..."
	@echo ""
	@echo "Step 1: Building Docker images..."
	docker compose -f docker-compose.prod.yml build
	@echo ""
	@echo "Step 2: Starting services..."
	docker compose -f docker-compose.prod.yml up -d
	@echo ""
	@echo "Step 3: Waiting for database to be ready..."
	@sleep 5
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		echo "Checking db (attempt $$i)..."; \
		docker compose -f docker-compose.prod.yml exec -T db pg_isready -U lms_user -d lms_db >/dev/null 2>&1 && break || sleep 2; \
	done
	@echo ""
	@echo "Step 4: Applying migrations..."
	@docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || true
	@echo ""
	@echo "============================================"
	@echo "✅ AI-LMS started successfully!"
	@echo ""
	@echo "🌐 Frontend: http://localhost"
	@echo "📚 API Docs: http://localhost/api/docs"
	@echo ""
	@echo "💡 Next: Create default users with:"
	@echo "   make create-users"
	@echo "============================================"

# Stop services
stop:
	@echo "Stopping services..."
	docker compose -f docker-compose.prod.yml down
	@echo "✓ Services stopped"

# Create default users
create-users:
	@echo "Creating default users..."
	@docker compose -f docker-compose.prod.yml exec -T backend python -c "\
from app.db.session import SessionLocal; \
from app.models.user import User; \
from app.utils.auth import get_password_hash; \
db = SessionLocal(); \
users = [ \
    ('admin@test.com', 'Admin User', 'admin'), \
    ('teacher@test.com', 'Teacher User', 'instructor'), \
    ('student@test.com', 'Student User', 'learner') \
]; \
for email, name, role in users: \
    existing = db.query(User).filter(User.email == email).first(); \
    if not existing: \
        user = User(email=email, full_name=name, hashed_password=get_password_hash('00000000'), role=role, is_active=True); \
        db.add(user); \
        print(f'✓ Created: {email}'); \
    else: \
        print(f'- Already exists: {email}'); \
db.commit(); \
print('Done!'); \
"
	@echo ""
	@echo "============================================"
	@echo "✅ Default users ready!"
	@echo ""
	@echo "🔑 Login credentials:"
	@echo "   Admin:   admin@test.com / 00000000"
	@echo "   Teacher: teacher@test.com / 00000000"
	@echo "   Student: student@test.com / 00000000"
	@echo "============================================"

# Restart services
restart:
	@echo "Restarting services..."
	docker compose -f docker-compose.prod.yml restart
	@echo "✓ Services restarted"

# Rebuild and restart
rebuild:
	@echo "Rebuilding and restarting..."
	docker compose -f docker-compose.prod.yml build
	docker compose -f docker-compose.prod.yml up -d
	@echo "✓ Rebuild complete"

# View logs
logs:
	docker compose -f docker-compose.prod.yml logs -f

logs-backend:
	docker compose -f docker-compose.prod.yml logs -f backend

logs-frontend:
	docker compose -f docker-compose.prod.yml logs -f frontend

logs-nginx:
	docker compose -f docker-compose.prod.yml logs -f nginx

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Images built"

# Clean up
clean:
	@echo "Cleaning up..."
	docker compose -f docker-compose.prod.yml down -v
	@echo "✓ All containers and volumes removed"

# Run migrations
migrate:
	@echo "Running database migrations..."
	docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
	@echo "✓ Migrations applied"

# Create new migration
migration:
	@echo "Creating new migration..."
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Error: MESSAGE is required. Usage: make migration MESSAGE='your message'"; \
		exit 1; \
	fi
	docker compose -f docker-compose.prod.yml exec backend alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "✓ Migration created"

# Shell access
shell-backend:
	docker compose -f docker-compose.prod.yml exec backend /bin/bash

shell-frontend:
	docker compose -f docker-compose.prod.yml exec frontend /bin/sh

shell-db:
	docker compose -f docker-compose.prod.yml exec db psql -U lms_user -d lms_db

# Testing (when implemented)
test:
	@echo "Running tests..."
	cd apps/backend && pytest tests/ -v

# Linting
lint:
	@echo "Running linters..."
	cd apps/backend && ruff check app/

# Format code
format:
	@echo "Formatting code..."
	cd apps/backend && ruff format app/
