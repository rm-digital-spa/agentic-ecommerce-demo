# ecommerce-agent

Strands agent for ecommerce operations (products, customers, orders, purchase
advice), extracted from the API so it can be deployed independently on AWS
AgentCore Runtime.

## Contract

Implements the AgentCore Runtime HTTP contract:

- `POST /invocations` — body `{"query", "session_id", "user": {"id","name","email"}}`,
  streams NDJSON message events.
- `GET /ping` — health check.

Extra endpoints used by the ecommerce API for chat history:

- `GET /sessions/{session_id}/messages?agent_id=ecommerce_agent`
- `DELETE /sessions/{session_id}`

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `ECOMMERCE_API_URL` | `http://localhost:8000` | Ecommerce API base URL (data operations) |
| `ECOMMERCE_API_USERNAME` / `ECOMMERCE_API_PASSWORD` | `admin` / `admin123` | Basic auth against the API |
| `SII_AGENT_URL` | `http://localhost:8002` | SII agent A2A endpoint |
| `ECOMMERCE_AGENT_PORT` | `8080` | Listen port (AgentCore expects 8080) |
| `AWS_REGION` | `us-east-1` | Bedrock region |
| `BEDROCK_MODEL_ID` | claude haiku 4.5 | Bedrock model |
| `BEDROCK_KB_ID` | *(empty = memory disabled)* | Knowledge Base for user preferences |
| `BEDROCK_KB_DATA_SOURCE_ID` | — | KB data source (CUSTOM/S3) |
| `BEDROCK_KB_S3_BUCKET` / `BEDROCK_KB_S3_PREFIX` | — / `memories/` | KB S3 storage |
| `SESSIONS_DIR` | `./sessions` | FileSessionManager storage (ephemeral) |
| `LANGFUSE_*` | — | Langfuse credentials/host |

## Run locally

```bash
uv run main.py
```
