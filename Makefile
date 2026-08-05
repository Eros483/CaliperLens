.PHONY: setup dev test style build clean infra-up infra-down dbt-run eval help

## Install all dependencies (frontend + backend)
setup:
	@echo "==> Installing frontend dependencies..."
	cd frontend && npm install
	@echo "==> Installing backend dependencies..."
	cd backend && uv sync

## Run frontend + backend dev servers concurrently
dev:
	@trap 'kill 0' EXIT; \
	cd backend && uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload & \
	cd frontend && npm run dev & \
	wait

## Run all tests (frontend + backend)
test:
	cd frontend && npm run test
	cd backend && uv run pytest

## Format + lint all code
style:
	cd frontend && npm run format && npm run lint
	cd backend && uv run ruff check . --fix && uv run ruff format .

## Production build of frontend
build:
	cd frontend && npm run build

## Remove build artifacts, caches, node_modules
clean:
	rm -rf frontend/dist frontend/node_modules
	rm -rf backend/__pycache__ backend/.pytest_cache backend/.venv backend/.ruff_cache
	rm -rf .venv __pycache__ .ruff_cache

## Start docker-compose services (Airflow, Prometheus, Grafana, Sandbox)
infra-up:
	docker-compose up -d

## Stop docker-compose services
infra-down:
	docker-compose down

## Run dbt models (MySQL -> DuckDB transforms)
dbt-run:
	cd dbt && dbt run

## Run the NL-to-SQL eval harness (schema check only, CI-safe)
eval:
	python eval/runner.py --check

## Show this help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
