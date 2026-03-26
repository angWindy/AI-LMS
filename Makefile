.PHONY: help setup dev-setup start stop restart logs build clean migrate migration test lint format

# Default target
help:
	@echo "LMS MVP - Available Commands:"
	@echo "  make setup          - Initial project setup (copy .env, install deps)"
	@echo "  make dev-setup      - Setup development environment"
	@echo "  make start          - Start all services with Docker Compose"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs only"
	@echo "  make build          - Build Docker images"
	@echo "  make clean          - Stop and remove all containers, volumes"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migration      - Create new migration (MESSAGE='your message')"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linting"
	@echo "  make format         - Format code"

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
