FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/appuser/.cache/huggingface

WORKDIR /app

COPY pyproject.toml ./

RUN python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch>=2.2,<3"

COPY backend ./backend

COPY ml/data/processed/train.csv ./ml/data/processed/train.csv

RUN python -m pip install --no-cache-dir --timeout 120 --retries 5 . \
    && python -m pip install --no-cache-dir --timeout 120 --retries 5 \
        "sentencepiece>=0.2,<1" \
        "transformers>=4.46,<5" \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app /home/appuser

EXPOSE 7860

USER appuser

ENTRYPOINT ["sh", "/app/backend/scripts/start.sh"]
