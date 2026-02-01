.PHONY: help install dev up down logs shell db-shell test lint format

ifneq (,$(wildcard .env))
    include .env
    export
endif

# Default target
help:
	@echo "Lazy Tasks - Personal AI Executive Assistant"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies with pip"
	@echo "  dev         Install dev dependencies"
	@echo "  conda-env   Create conda environment"
	@echo ""
	@echo "Docker:"
	@echo "  up          Start all services"
	@echo "  up-build    Build and start all services"
	@echo "  down        Stop all services"
	@echo "  logs        View logs (follow mode)"
	@echo "  shell       Open shell in app container"
	@echo "  db-shell    Open PostgreSQL shell"
	@echo ""
	@echo "Development:"
	@echo "  run         Run app locally (without Docker)"
	@echo "  test        Run tests"
	@echo "  lint        Run linter"
	@echo "  format      Format code"
	@echo "  typecheck   Run type checker"
	@echo ""
	@echo "Database:"
	@echo "  db-migrate  Run database migrations"
	@echo "  db-reset    Reset database (WARNING: destroys data)"

# Setup
install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

conda-env:
	conda env create -f environment.yml
	@echo "Run: conda activate lazy-tasks"
		docker compose exec -T postgres psql -U lazy_tasks -d lazy_tasks -f /docker-entrypoint-initdb.d/init.sql
start:
	bash scripts/start.sh

# Docker commands
up:
	docker compose up -d

up-build:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-app:
	docker compose logs -f app
shell:
	docker compose exec app /bin/bash

db-shell:
	docker compose exec postgres psql -U lazy_tasks -d lazy_tasks

# Development
run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest tests/ -v

lint:
	ruff check app/

format:
	ruff format app/
	ruff check app/ --fix

typecheck:
	mypy app/

# Database
PYTHON ?= python3

db-migrate:
	$(PYTHON) -m alembic upgrade head

db-reset:
	docker compose down -v
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL..."
	sleep 5
	docker compose up -d

# Telegram webhook
webhook-set:
	@echo "Setting webhook to: $(URL)"
	curl -X POST "https://api.telegram.org/bot$(TELEGRAM_BOT_TOKEN)/setWebhook" \
		-H "Content-Type: application/json" \
		-d '{"url": "$(URL)/webhook/telegram", "secret_token": "$(TELEGRAM_WEBHOOK_SECRET)"}'

webhook-info:
	curl "https://api.telegram.org/bot$(TELEGRAM_BOT_TOKEN)/getWebhookInfo"

webhook-delete:
	curl -X POST "https://api.telegram.org/bot$(TELEGRAM_BOT_TOKEN)/deleteWebhook"
