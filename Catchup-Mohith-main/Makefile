# /home/mohith/Catchup-Mohith/Makefile
.PHONY: dev dev-clean test-unit test-int test-all lint \
        migrate seed-demo shell-api shell-db logs-api \
        logs-worker stop

dev:
	docker compose up --build

dev-clean:
	docker compose down -v && docker compose up --build

test-unit:
	pytest backend/tests/unit/

test-int:
	pytest backend/tests/integration/

test-all:
	pytest backend/tests/

lint:
	ruff check backend/ && black --check backend/

migrate:
	alembic -c backend/alembic.ini upgrade head

seed-demo:
	python -m backend.scripts.seed_demo

shell-api:
	docker compose exec api bash

shell-db:
	docker compose exec db psql -U stockbridge

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f temporal-worker

stop:
	docker compose down
