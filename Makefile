.PHONY: up down restart logs shell-backend shell-db migrate seed test lint pull-models

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart $(svc)

logs:
	docker compose logs -f $(svc)

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U onegov -d onegov_ai

migrate:
	docker compose exec backend alembic upgrade head

new-migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec backend python scripts/seed.py

test:
	docker compose exec backend pytest tests/ -v --tb=short

lint:
	docker compose exec backend ruff check .

pull-models:
	docker compose exec ollama ollama pull llama3.2
	docker compose exec ollama ollama pull nomic-embed-text
