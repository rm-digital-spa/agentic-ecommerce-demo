"""Ecommerce agent service.

Exposes the AWS AgentCore Runtime HTTP contract:
- POST /invocations : run the agent, streaming NDJSON message events.
- GET  /ping        : health check.

Plus session endpoints so the API can read/delete conversation history
(sessions are stored by FileSessionManager inside this service).
"""

import json
import logging
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langfuse import get_client, observe, propagate_attributes
from pydantic import BaseModel
from strands import tool

from agent import build_ecommerce_agent, get_session
from sii_transport import invoke_sii_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_PORT = int(os.getenv("ECOMMERCE_AGENT_PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

app = FastAPI()


class UserPayload(BaseModel):
    id: str
    name: str
    email: str


class InvocationPayload(BaseModel):
    query: str
    session_id: str
    user: UserPayload


@app.get("/ping")
def ping():
    return {"status": "healthy", "service": "ecommerce-agent"}


@observe()
@app.post("/invocations")
async def invocations(payload: InvocationPayload):
    user = payload.user.model_dump()

    async def event_generator():
        # Keep Langfuse context active for the full lifecycle of streamed events.
        with propagate_attributes(
            user_id=user["email"], session_id=payload.session_id
        ):
            if hasattr(langfuse, "update_current_trace"):
                langfuse.update_current_trace(user_id=user["email"])

            @tool
            def sii_assistant(query: str) -> str:
                """Ask the SII agent about companies and invoices."""
                try:
                    return invoke_sii_agent(query)
                except Exception as e:
                    logger.error(f"Error invoking SII agent: {e}")
                    return "Error invoking agent."

            agent = build_ecommerce_agent(
                tools=[sii_assistant],
                session_id=payload.session_id,
                user=user,
            )
            logger.info("Ecommerce agent initialized: %s", agent.name)

            try:
                async for event in agent.stream_async(payload.query):
                    # Emit one JSON object per line (NDJSON): agent messages,
                    # tool calls and tool responses.
                    if isinstance(event, dict) and "message" in event:
                        yield f"{json.dumps(event['message'])}\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"{json.dumps({'error': str(e)})}\n"

    return StreamingResponse(
        event_generator(),
        media_type="application/x+ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ---- Session endpoints (conversation history lives in this service) ----


@app.get("/sessions/{session_id}/messages")
def session_messages(session_id: str, agent_id: str = "ecommerce_agent"):
    session = get_session(session_id=session_id)
    try:
        messages = session.list_messages(session_id=session_id, agent_id=agent_id)
    except Exception as e:
        logger.error(f"Error reading session {session_id}: {e}")
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": [msg.message for msg in messages],
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    session = get_session(session_id=session_id)
    session.delete_session(session_id=session_id)
    return {"message": "Session deleted successfully."}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=AGENT_PORT)
