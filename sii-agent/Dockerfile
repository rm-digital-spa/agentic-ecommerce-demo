# Build from the repo root: docker build -f sii-agent/Dockerfile .
# Repo-root context is required because this component depends on common/.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /repo
COPY common/ common/
COPY sii-agent/ sii-agent/

WORKDIR /repo/sii-agent
RUN uv sync

# AgentCore Runtime requires the container to listen on 8080 and serve
# GET /ping + POST /invocations. Locally (devenv) this stays on 8002.
ENV SII_AGENT_PORT=8080
EXPOSE 8080
CMD ["uv", "run", "main.py"]
