FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/models

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /models \
    && chown app:app /models

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations

RUN python -m pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        'torch==2.12.1' \
    && python -m pip install --no-cache-dir '.[ai]'

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn enterprise_ai_platform.api:app --host 0.0.0.0 --port 8000"]
