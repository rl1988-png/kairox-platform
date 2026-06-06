.PHONY: dev build test lint format typecheck migrate seed docker-up docker-down install

install:
	pnpm install
	cd packages/ai-gateway && pip install -e ".[dev]"
	cd apps/api && pip install -e ".[dev]"

dev:
	pnpm dev

build:
	pnpm build

test:
	pnpm test

lint:
	pnpm lint

format:
	pnpm format

typecheck:
	pnpm typecheck

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python -m kairox_api.scripts.seed

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f
