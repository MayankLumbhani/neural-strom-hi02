.PHONY: dev test lint format migrate

dev:
	python -m uvicorn grievance.main:app --app-dir backend/src --reload

test:
	python -m pytest

lint:
	python -m ruff check backend/src backend/tests
	python -m ruff format --check backend/src backend/tests
	python -m mypy backend/src

format:
	python -m ruff format backend/src backend/tests

migrate:
	python -m alembic -c backend/alembic.ini upgrade head
