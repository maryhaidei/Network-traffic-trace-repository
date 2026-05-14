FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY tests /app/tests


ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_NO_CACHE_DIR=1

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-build-isolation -e ".[dev]"

CMD ["bash", "-lc", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]