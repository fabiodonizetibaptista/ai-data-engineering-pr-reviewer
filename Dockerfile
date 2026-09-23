FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --requirement requirements.txt

COPY --chown=app:app src ./src
COPY --chown=app:app rules ./rules

USER app

CMD ["sh", "-c", "python -m uvicorn github_app.webhook:app --app-dir src --host 0.0.0.0 --port ${PORT:-8000}"]