# Build from the repo root: docker build -f sii-mcp/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /repo/sii-mcp
COPY sii-mcp/pyproject.toml ./
RUN uv sync --no-install-project

COPY sii-mcp/ ./
RUN uv sync

# The JSON data ships inside the image; writes are ephemeral by design
ENV SII_DATA_PATH=/repo/sii-mcp/data/sii_data.json

EXPOSE 8001
ENV SII_MCP_PORT=8001
CMD ["uv", "run", "python", "main.py"]
