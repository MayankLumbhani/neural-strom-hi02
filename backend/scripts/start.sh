#!/bin/sh
set -eu

PORT="${PORT:-7860}"

python -m alembic -c backend/alembic.ini upgrade head
exec python -m uvicorn grievance.main:app \
    --app-dir backend/src \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1
