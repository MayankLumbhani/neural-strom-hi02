.PHONY: dev test lint format migrate seed generate-dataset

dev:
	python -m uvicorn grievance.main:app --app-dir backend/src --reload

test:
	python -m pytest

lint:
	python -m ruff check backend/src backend/tests ml/src ml/tests
	python -m ruff format --check backend/src backend/tests ml/src ml/tests
	python -m mypy backend/src ml/src

format:
	python -m ruff format backend/src backend/tests ml/src ml/tests

migrate:
	python -m alembic -c backend/alembic.ini upgrade head

seed:
	python -m grievance.seed

generate-dataset:
	python -m ml.src.generate_dataset
