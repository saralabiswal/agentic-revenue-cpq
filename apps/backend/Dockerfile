FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY apps ./apps
COPY configs ./configs
COPY integrations ./integrations
COPY schemas ./schemas
COPY services ./services

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
