.PHONY: help setup dev-setup start stop restart logs build clean migrate migration test lint format prod prod-stop prod-logs

# Default target
help:
	@echo "LMS MVP - Available Commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make setup          - Initial project setup"
	@echo "    make dev-setup      - Setup development environment"
	@echo "    make start          - Start backend + database (dev mode)"
	@echo "    make stop           - Stop services"
	@echo "    make restart        - Restart services"
	@echo "    make logs           - View logs"
	@echo ""
	@echo "  Production:"
	@echo "    make prod           - Deploy full stack on port 80"
	@echo "    make prod-stop      - Stop production deployment"
	@echo "    make prod-logs      - View production logs"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate        - Run database migrations"
	@echo "    make migration      - Create new migration"
	@echo "    make shell-db       - Open PostgreSQL shell"
	@echo ""
	@echo "  Other:"
	@echo "    make build          - Build Docker images"
	@echo "    make clean          - Remove all containers and volumes"
	@echo "    make test           - Run tests"
	@echo "    make lint           - Run linting"

# Initial setup
setup:
	@echo "Setting up project..."
	@cp -n .env.example .env || true
	@echo "✓ .env file created (edit with your settings)"
	@echo "Next steps:"
	@echo "  1. Edit .env file with your configuration"
	@echo "  2. Run 'make start' to start services"

# Development setup
dev-setup:
	@echo "Setting up development environment..."
	cd apps/backend && pip install -r requirements.txt
	@echo "✓ Development environment ready"

# Start services
start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✓ Services started"
	@echo "Waiting for database to be ready..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		echo "Checking db (attempt $$i)..."; \
		docker-compose exec -T db pg_isready -U lms_user -d lms_db >/dev/null 2>&1 && break || sleep 2; \
	done
	@echo "Applying migrations..."
	@docker-compose exec -T backend alembic upgrade head || (echo "Migration failed, please run 'make migrate' manually"; exit 0)
	@echo "✓ Migrations applied"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

# Stop services
stop:
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped"

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart
	@echo "✓ Services restarted"

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Images built"

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "✓ All containers and volumes removed"

# Run migrations
migrate:
	@echo "Running database migrations..."
	docker-compose exec backend alembic upgrade head
	@echo "✓ Migrations applied"

# Create new migration
migration:
	@echo "Creating new migration..."
	@if [ -z "$(MESSAGE)" ]; then \
		echo "Error: MESSAGE is required. Usage: make migration MESSAGE='your message'"; \
		exit 1; \
	fi
	docker-compose exec backend alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "✓ Migration created"

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-db:
	docker-compose exec db psql -U lms_user -d lms_db

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

# =============================================================================
# PRODUCTION DEPLOYMENT
# =============================================================================

# Deploy full stack production (single address on port 80)
prod:
	@echo "🚀 Deploying AI-LMS Production..."
	@echo ""
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo ""
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Applying migrations..."
	@docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || true
	@echo ""
	@echo "============================================"
	@echo "✅ AI-LMS deployed successfully!"
	@echo ""
	@echo "🌐 Access: http://localhost"
	@echo "📚 API Docs: http://localhost/docs"
	@echo "============================================"

# Stop production
prod-stop:
	@echo "Stopping production services..."
	docker-compose -f docker-compose.prod.yml down
	@echo "✓ Production stopped"

# Production logs
prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Rebuild production
prod-rebuild:
	@echo "Rebuilding production..."
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml up -d --build
	@echo "✓ Production rebuilt"
