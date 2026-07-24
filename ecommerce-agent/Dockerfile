# Build from the repo root: docker build -f ecommerce-agent/Dockerfile .
# Repo-root context is required because this component depends on common/.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /repo
COPY common/ common/
COPY ecommerce-agent/ ecommerce-agent/

WORKDIR /repo/ecommerce-agent
RUN uv sync

ENV SESSIONS_DIR=/data/sessions
RUN mkdir -p /data/sessions

# AgentCore Runtime expects the service on port 8080
EXPOSE 8080
CMD ["uv", "run", "main.py"]
