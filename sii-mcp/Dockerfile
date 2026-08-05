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

# AgentCore Runtime's MCP contract: the server must listen on 8000 and serve
# the MCP protocol at /mcp. (The HTTP agent contract is a different shape:
# port 8080 with /invocations + /ping.) Locally devenv keeps this on 8001.
ENV SII_MCP_PORT=8000
# AgentCore load-balances across instances, so no request may depend on
# server-side session state.
ENV MCP_STATELESS_HTTP=true
EXPOSE 8000
CMD ["uv", "run", "python", "main.py"]
