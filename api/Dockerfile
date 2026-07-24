# Build from the repo root: docker build -f api/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /repo/api
COPY api/pyproject.toml ./
RUN uv sync --no-install-project

COPY api/ ./
RUN uv sync

# SQLite lives inside the container (ephemeral by design; seeded on startup)
ENV DB_PATH=/data/ecommerce.db
RUN mkdir -p /data

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "main.py", "--port", "8000"]
