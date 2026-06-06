FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages/ai-gateway/pyproject.toml packages/ai-gateway/README.md /app/packages/ai-gateway/
COPY packages/ai-gateway/src /app/packages/ai-gateway/src
RUN pip install --no-cache-dir /app/packages/ai-gateway

COPY apps/api/pyproject.toml /app/apps/api/
COPY apps/api/src /app/apps/api/src
COPY apps/api/alembic.ini /app/apps/api/alembic.ini
COPY apps/api/alembic /app/apps/api/alembic
COPY apps/api/docker-entrypoint.sh /app/apps/api/docker-entrypoint.sh

WORKDIR /app/apps/api

RUN pip install --no-cache-dir . \
    && chmod +x /app/apps/api/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/apps/api/docker-entrypoint.sh"]
CMD ["uvicorn", "kairox_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
