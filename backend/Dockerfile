FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import email_validator, bcrypt; print('deps-ok', email_validator.__version__, bcrypt.__version__)"

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD sh -c "alembic upgrade head && python -m app.seed && python -m app.readiness.backfill && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
