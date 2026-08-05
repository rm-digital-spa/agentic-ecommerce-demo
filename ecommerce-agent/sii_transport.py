"""Transport for reaching the SII agent.

The SII agent is the same service in both cases, but how you reach it depends
on where it runs:

- ``a2a``       — direct HTTP against its A2A endpoint. Used locally, where
                  both agents are plain processes (``devenv up``).
- ``agentcore`` — AWS AgentCore Runtime does not expose the container as a
                  reachable HTTP endpoint; you call the InvokeAgentRuntime API
                  with the runtime ARN and the service dispatches to the
                  container's ``/invocations``.

Select with ``SII_AGENT_TRANSPORT``; it defaults to ``a2a`` so local
development keeps working unchanged.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

SII_AGENT_TRANSPORT = os.getenv("SII_AGENT_TRANSPORT", "a2a").lower()
SII_AGENT_URL = os.getenv("SII_AGENT_URL", "http://localhost:8002")
SII_AGENT_RUNTIME_ARN = os.getenv("SII_AGENT_RUNTIME_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

_a2a_agent = None
_agentcore_client = None


def _invoke_a2a(query: str) -> str:
    global _a2a_agent
    if _a2a_agent is None:
        from strands.agent.a2a_agent import A2AAgent

        _a2a_agent = A2AAgent(endpoint=SII_AGENT_URL)
    return str(_a2a_agent(query))


def _invoke_agentcore(query: str) -> str:
    global _agentcore_client
    if not SII_AGENT_RUNTIME_ARN:
        raise ValueError(
            "SII_AGENT_TRANSPORT=agentcore requires SII_AGENT_RUNTIME_ARN."
        )
    if _agentcore_client is None:
        import boto3

        _agentcore_client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)

    response = _agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=SII_AGENT_RUNTIME_ARN,
        payload=json.dumps({"prompt": query}).encode("utf-8"),
    )

    body = response.get("response")
    raw = body.read() if hasattr(body, "read") else body
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    # The container returns {"result": "..."}; fall back to the raw body if the
    # shape ever changes so the tool degrades instead of breaking.
    try:
        return str(json.loads(raw).get("result", raw))
    except (ValueError, AttributeError):
        return str(raw)


def invoke_sii_agent(query: str) -> str:
    """Send a query to the SII agent over the configured transport."""
    if SII_AGENT_TRANSPORT == "agentcore":
        return _invoke_agentcore(query)
    if SII_AGENT_TRANSPORT != "a2a":
        logger.warning(
            "Unknown SII_AGENT_TRANSPORT %r, falling back to a2a.",
            SII_AGENT_TRANSPORT,
        )
    return _invoke_a2a(query)
